import { nanoid } from 'nanoid';
import { db } from '../db/index.js';

/**
 * Service BYOP - Bring Your Own Post
 * Permet aux partenaires de créer leurs propres contenus avec partage automatisé
 */

export const BYOP_CONFIG = {
  DEFAULT_REVSHARE_PCT: 0.40,
  DEFAULT_HASHTAGS: '#ia #tools #productivité',
  SHARE_EMAIL_DAILY_LIMIT: 200
};

/**
 * Crée un asset pour BYOP avec métadonnées spécifiques
 */
export async function createAssetForByop(partnerId, sourceUrl, title, description, hashtags, cta) {
  const assetId = nanoid();
  
  const meta = {
    source: "byop",
    owner_partner_id: partnerId,
    title: title || "",
    description: description || "",
    hashtags: hashtags || BYOP_CONFIG.DEFAULT_HASHTAGS,
    cta: cta || "",
    created_via: "byop_submission"
  };
  
  if (sourceUrl) {
    meta.download_url = sourceUrl;
  }
  
  // Simuler la création d'asset dans la base
  const mockAsset = {
    id: assetId,
    status: "new",
    meta_json: JSON.stringify(meta),
    created_at: new Date().toISOString()
  };
  
  return { assetId, meta };
}

/**
 * Enregistre une soumission BYOP
 */
export async function registerByopSubmission(partnerId, sourceUrl, title, description, hashtags, cta, assetId) {
  const submissionId = nanoid();
  
  const submission = {
    id: submissionId,
    partner_id: partnerId,
    source_url: sourceUrl || "",
    title: title || "",
    description: description || "",
    hashtags: hashtags || "",
    cta: cta || "",
    asset_id: assetId,
    status: "processing",
    revshare_pct: BYOP_CONFIG.DEFAULT_REVSHARE_PCT,
    created_at: new Date().toISOString()
  };
  
  // Simuler l'enregistrement en base
  return submissionId;
}

/**
 * Récupère une soumission BYOP par ID et partenaire
 */
export async function getByopSubmission(submissionId, partnerId) {
  // Simulation - en production cela viendrait de la base de données
  return {
    id: submissionId,
    partner_id: partnerId,
    title: "Titre du contenu BYOP",
    description: "Description du contenu créé par le partenaire",
    hashtags: "#ia #tools #productivité",
    cta: "Découvre cet outil incroyable →",
    asset_id: nanoid(),
    status: "ready",
    revshare_pct: 0.40,
    created_at: new Date().toISOString()
  };
}

/**
 * Met à jour le statut d'une soumission BYOP
 */
export async function updateByopStatus(submissionId, status) {
  // Simulation - en production cela mettrait à jour la base
  return true;
}