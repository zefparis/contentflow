import { nanoid } from 'nanoid';

/**
 * Service ShareKit - Outils de partage pour les partenaires
 * Génère des liens courts, intentions de partage et gère les logs
 */

/**
 * Crée un lien court pour un asset avec tracking partenaire
 */
export function createShortlink(assetId, partnerId) {
  // En production, cela utiliserait un service de liens courts
  const shortCode = nanoid(8);
  return {
    short_url: `/l/${shortCode}`,
    original_url: `/asset/${assetId}?pid=${partnerId}`,
    clicks: 0,
    created_at: new Date().toISOString()
  };
}

/**
 * Construit le texte de partage formaté
 */
export function buildShareText(title, cta, shortUrl, hashtags) {
  const cleanTitle = (title || "Découverte utile").trim();
  const cleanCta = (cta || "Découvre ici →").trim();
  const cleanHashtags = hashtags && hashtags.trim() ? ` ${hashtags.trim()}` : "";
  
  return `${cleanTitle}\n\n${cleanCta} ${shortUrl}${cleanHashtags}`;
}

/**
 * Génère les URLs d'intention de partage pour différentes plateformes
 */
export function getShareIntents(shortUrl, text) {
  const encodedText = encodeURIComponent(text);
  const encodedUrl = encodeURIComponent(shortUrl);
  
  return {
    whatsapp: `https://wa.me/?text=${encodedText}`,
    telegram: `https://t.me/share/url?url=${encodedUrl}&text=${encodedText}`,
    twitter: `https://twitter.com/intent/tweet?url=${encodedUrl}&text=${encodedText}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`,
    copy: text
  };
}

/**
 * Enregistre une action de partage
 */
export async function logShare(partnerId, channel, recipientsCount = 0, message = "") {
  const logId = nanoid();
  
  const shareLog = {
    id: logId,
    partner_id: partnerId,
    channel: channel,
    recipients_count: recipientsCount,
    message: message.substring(0, 2000), // Limite à 2000 caractères
    created_at: new Date().toISOString()
  };
  
  // En production, cela sauvegarderait en base de données
  console.log(`Share logged: ${channel} by partner ${partnerId}`);
  return logId;
}

/**
 * Compte les emails envoyés par un partenaire dans les dernières 24h
 */
export async function getDailyEmailCount(partnerId) {
  // En production, cela ferait une requête à la base
  return 0; // Simulation - retourne 0 pour permettre l'envoi
}

/**
 * Valide une liste d'emails
 */
export function validateEmails(emailString) {
  if (!emailString || !emailString.trim()) {
    return [];
  }
  
  const emails = emailString
    .replace(/;/g, ',')
    .split(',')
    .map(email => email.trim())
    .filter(email => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return email && emailRegex.test(email);
    });
  
  return emails;
}

/**
 * Génère le HTML d'email pour partage BYOP
 */
export function generateEmailHTML(title, text, isAd = true) {
  const formattedText = text.replace(/\n/g, '<br>');
  const adDisclaimer = isAd ? '<p style="font-size:12px;opacity:.7;margin-top:20px;">#ad • Vous pouvez vous désinscrire à tout moment.</p>' : '';
  
  return `
    <div style="font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #333; margin-bottom: 20px;">${title}</h2>
      <div style="color: #555; line-height: 1.6;">
        ${formattedText}
      </div>
      ${adDisclaimer}
    </div>
  `;
}