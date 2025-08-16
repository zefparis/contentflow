import express from 'express';
import { createAssetForByop, registerByopSubmission, getByopSubmission } from '../services/byop.js';
import { createShortlink, buildShareText, getShareIntents, logShare, getDailyEmailCount, validateEmails, generateEmailHTML } from '../services/sharekit.js';

const router = express.Router();

// Configuration BYOP depuis les variables d'environnement
const FEATURE_BYOP = process.env.FEATURE_BYOP === 'true';
const SHARE_EMAIL_ENABLED = process.env.SHARE_EMAIL_ENABLED === 'true';
const SHARE_EMAIL_DAILY_LIMIT = parseInt(process.env.SHARE_EMAIL_DAILY_LIMIT || '200');

// Middleware pour vérifier l'authentification partenaire
function requirePartnerAuth(req, res, next) {
  const partnerId = req.session?.partnerId || req.headers['x-partner-id'];
  if (!partnerId) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  req.partnerId = partnerId;
  next();
}

// GET /api/byop/config - Configuration BYOP
router.get('/config', (req, res) => {
  res.json({
    enabled: FEATURE_BYOP,
    share_email_enabled: SHARE_EMAIL_ENABLED,
    share_email_daily_limit: SHARE_EMAIL_DAILY_LIMIT,
    default_hashtags: process.env.SHAREKIT_DEFAULT_HASHTAGS || '#ia #tools #productivité'
  });
});

// POST /api/byop/submit - Soumettre un nouveau contenu BYOP
router.post('/submit', requirePartnerAuth, async (req, res) => {
  if (!FEATURE_BYOP) {
    return res.status(404).json({ error: 'BYOP feature disabled' });
  }

  try {
    const { source_url, title, description, hashtags, cta } = req.body;
    const partnerId = req.partnerId;

    // Créer l'asset
    const { assetId, meta } = await createAssetForByop(
      partnerId,
      source_url?.trim() || null,
      title || '',
      description || '',
      hashtags || '',
      cta || ''
    );

    // Enregistrer la soumission
    const submissionId = await registerByopSubmission(
      partnerId,
      source_url?.trim() || null,
      title || '',
      description || '',
      hashtags || '',
      cta || '',
      assetId
    );

    res.json({
      success: true,
      submission_id: submissionId,
      asset_id: assetId,
      meta
    });
  } catch (error) {
    console.error('BYOP submission error:', error);
    res.status(500).json({ error: 'Failed to create BYOP submission' });
  }
});

// GET /api/byop/submissions/:id - Récupérer une soumission
router.get('/submissions/:id', requirePartnerAuth, async (req, res) => {
  if (!FEATURE_BYOP) {
    return res.status(404).json({ error: 'BYOP feature disabled' });
  }

  try {
    const { id } = req.params;
    const partnerId = req.partnerId;

    const submission = await getByopSubmission(id, partnerId);
    if (!submission) {
      return res.status(404).json({ error: 'Submission not found' });
    }

    res.json({ success: true, data: submission });
  } catch (error) {
    console.error('Get BYOP submission error:', error);
    res.status(500).json({ error: 'Failed to get submission' });
  }
});

// POST /api/byop/share-kit/:id - Générer le kit de partage
router.post('/share-kit/:id', requirePartnerAuth, async (req, res) => {
  if (!FEATURE_BYOP) {
    return res.status(404).json({ error: 'BYOP feature disabled' });
  }

  try {
    const { id } = req.params;
    const partnerId = req.partnerId;

    const submission = await getByopSubmission(id, partnerId);
    if (!submission) {
      return res.status(404).json({ error: 'Submission not found' });
    }

    // Créer le lien court
    const shortlink = createShortlink(submission.asset_id, partnerId);
    const baseUrl = process.env.APP_BASE_URL || 'http://localhost:5000';
    const fullShortUrl = `${baseUrl}${shortlink.short_url}`;

    // Construire le texte de partage
    const shareText = buildShareText(
      submission.title || 'Découverte utile',
      submission.cta || 'Découvre ici →',
      fullShortUrl,
      submission.hashtags || process.env.SHAREKIT_DEFAULT_HASHTAGS
    );

    // Générer les intentions de partage
    const shareIntents = getShareIntents(fullShortUrl, shareText);

    res.json({
      success: true,
      data: {
        submission,
        short_url: fullShortUrl,
        share_text: shareText,
        share_intents: shareIntents
      }
    });
  } catch (error) {
    console.error('Share kit generation error:', error);
    res.status(500).json({ error: 'Failed to generate share kit' });
  }
});

// POST /api/byop/log-share - Logger une action de partage
router.post('/log-share', requirePartnerAuth, async (req, res) => {
  try {
    const { channel, recipients_count = 0, message = '' } = req.body;
    const partnerId = req.partnerId;

    await logShare(partnerId, channel, recipients_count, message);

    res.json({ success: true });
  } catch (error) {
    console.error('Log share error:', error);
    res.status(500).json({ error: 'Failed to log share action' });
  }
});

// POST /api/byop/email-share - Partager par email
router.post('/email-share', requirePartnerAuth, async (req, res) => {
  if (!SHARE_EMAIL_ENABLED) {
    return res.status(400).json({ error: 'Email sharing disabled' });
  }

  try {
    const { submission_id, emails } = req.body;
    const partnerId = req.partnerId;

    // Vérifier la limite quotidienne
    const dailyCount = await getDailyEmailCount(partnerId);
    if (dailyCount >= SHARE_EMAIL_DAILY_LIMIT) {
      return res.status(429).json({ error: 'Daily email limit reached' });
    }

    // Valider les emails
    const emailList = validateEmails(emails);
    if (emailList.length === 0) {
      return res.status(400).json({ error: 'No valid emails provided' });
    }

    // Récupérer la soumission
    const submission = await getByopSubmission(submission_id, partnerId);
    if (!submission) {
      return res.status(404).json({ error: 'Submission not found' });
    }

    // Créer le lien court et le texte
    const shortlink = createShortlink(submission.asset_id, partnerId);
    const baseUrl = process.env.APP_BASE_URL || 'http://localhost:5000';
    const fullShortUrl = `${baseUrl}${shortlink.short_url}`;
    
    const shareText = buildShareText(
      submission.title || 'Découverte utile',
      submission.cta || 'Découvre ici →',
      fullShortUrl,
      submission.hashtags || process.env.SHAREKIT_DEFAULT_HASHTAGS
    );

    // Logger l'action de partage
    await logShare(partnerId, 'email', emailList.length, shareText);

    // En production, ici on enverrait les emails via Brevo
    // Pour l'instant, on simule l'envoi
    console.log(`Would send emails to ${emailList.length} recipients:`, emailList);

    res.json({
      success: true,
      sent_count: emailList.length,
      remaining_daily_quota: SHARE_EMAIL_DAILY_LIMIT - dailyCount - emailList.length
    });
  } catch (error) {
    console.error('Email share error:', error);
    res.status(500).json({ error: 'Failed to send emails' });
  }
});

// GET /api/byop/submissions - Lister les soumissions du partenaire
router.get('/submissions', requirePartnerAuth, async (req, res) => {
  if (!FEATURE_BYOP) {
    return res.status(404).json({ error: 'BYOP feature disabled' });
  }

  try {
    const partnerId = req.partnerId;
    
    // En production, récupérer depuis la base de données
    // Pour l'instant, retourner des données de démo
    const submissions = [
      {
        id: 'demo-sub-1',
        partner_id: partnerId,
        title: 'Mon premier contenu BYOP',
        description: 'Un super outil que j\'ai découvert',
        hashtags: '#ia #tools #productivité',
        cta: 'Teste cet outil →',
        status: 'ready',
        created_at: new Date().toISOString()
      }
    ];

    res.json({ success: true, data: submissions });
  } catch (error) {
    console.error('List submissions error:', error);
    res.status(500).json({ error: 'Failed to list submissions' });
  }
});

export default router;