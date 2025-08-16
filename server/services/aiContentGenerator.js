// AI Content Generator Service
// Uses OpenAI to generate social media content from user files and messages

import OpenAI from 'openai';
import ContentModerationService from './contentModerationService.js';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

class AIContentGeneratorService {
  constructor() {
    this.moderationService = new ContentModerationService();
  }

  async generateContent(files, userMessage = '', targetPlatforms = ['instagram', 'tiktok', 'youtube']) {
    try {
      // Generate base content
      const generatedContent = await this.createContent(files, userMessage, targetPlatforms);
      
      // Moderate content for compliance
      const fullText = `${generatedContent.title} ${generatedContent.description} ${generatedContent.hashtags} ${generatedContent.cta}`;
      const moderationResult = await this.moderationService.analyzeContent(fullText, files);

      // Calculate quality score
      const qualityScore = this.moderationService.getContentQualityScore(generatedContent);

      return {
        ...generatedContent,
        compliance_score: moderationResult.score,
        flagged_issues: moderationResult.issues,
        approved: moderationResult.approved,
        quality_score: qualityScore,
        moderation_details: moderationResult.details
      };
    } catch (error) {
      console.error('Content generation error:', error);
      throw new Error('Impossible de générer le contenu');
    }
  }

  async createContent(files, userMessage, targetPlatforms) {
    const fileDescriptions = files.map(file => ({
      name: file.originalname || file.name || 'fichier_upload',
      type: (file.mimetype || file.type || '').startsWith('image/') ? 'image' : 'video',
      size_mb: ((file.size || 0) / 1024 / 1024).toFixed(1)
    }));

    const prompt = `Tu es un expert en création de contenu viral pour les réseaux sociaux.

Contexte:
- Message utilisateur: "${userMessage || 'Aucun message spécifique'}"
- Fichiers fournis: ${JSON.stringify(fileDescriptions)}
- Plateformes cibles: ${targetPlatforms.join(', ')}

Mission: Créer un post engageant qui génère des vues, likes, partages et commentaires.

IMPORTANT - Stratégies pour maximiser l'engagement:
1. Titre accrocheur avec émotions fortes (curiosité, surprise, joie)
2. Description qui raconte une histoire ou pose une question
3. Hashtags mélangant tendance + niche spécifique  
4. Call-to-action qui incite à l'interaction

Réponds uniquement avec un JSON dans ce format exact:
{
  "title": "Titre accrocheur de 40-80 caractères",
  "description": "Description engageante de 100-300 caractères avec émojis pertinents",
  "hashtags": "8-12 hashtags pertinents séparés par des espaces",
  "cta": "Call-to-action qui incite à commenter/partager (20-50 caractères)",
  "hook_strategy": "Stratégie utilisée pour accrocher l'audience",
  "engagement_prediction": "Prédiction d'engagement (faible/moyen/élevé)"
}

Exemples de hooks efficaces:
- "Vous ne devinerez jamais ce qui s'est passé..."
- "La méthode que personne ne vous dit..."
- "J'ai testé pendant 30 jours et voici le résultat..."
- "POV: tu découvres ce secret..."`;

    const response = await openai.chat.completions.create({
      model: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
      messages: [
        {
          role: "system",
          content: "Tu es un expert en marketing digital et création de contenu viral. Tu créés du contenu optimisé pour maximiser l'engagement et la portée organique."
        },
        {
          role: "user",
          content: prompt
        }
      ],
      response_format: { type: "json_object" },
      temperature: 0.8 // Créativité élevée pour le contenu
    });

    const result = JSON.parse(response.choices[0].message.content);
    
    // Validate and clean result
    return {
      title: this.validateAndTruncate(result.title, 100),
      description: this.validateAndTruncate(result.description, 500),
      hashtags: this.cleanHashtags(result.hashtags),
      cta: this.validateAndTruncate(result.cta, 100),
      hook_strategy: result.hook_strategy || 'Curiosité',
      engagement_prediction: result.engagement_prediction || 'moyen'
    };
  }

  validateAndTruncate(text, maxLength) {
    if (!text || typeof text !== 'string') return '';
    return text.trim().substring(0, maxLength);
  }

  cleanHashtags(hashtags) {
    if (!hashtags) return '';
    
    return hashtags
      .split(/[\s,]+/)
      .filter(tag => tag.startsWith('#') && tag.length > 1)
      .slice(0, 12) // Max 12 hashtags
      .join(' ');
  }

  // Generate variations for A/B testing
  async generateVariations(baseContent, count = 3) {
    const variations = [];
    
    for (let i = 0; i < count; i++) {
      const prompt = `Créer une variation du contenu suivant en gardant le même thème mais avec une approche différente:

Contenu original:
- Titre: ${baseContent.title}
- Description: ${baseContent.description}
- Hashtags: ${baseContent.hashtags}
- CTA: ${baseContent.cta}

Nouvelle variation avec une approche différente (plus émotionnel, plus factuel, plus humoristique, etc.).

Réponds avec un JSON:
{
  "title": "Nouveau titre",
  "description": "Nouvelle description", 
  "hashtags": "Nouveaux hashtags",
  "cta": "Nouveau CTA",
  "variation_type": "Type d'approche utilisée"
}`;

      try {
        const response = await openai.chat.completions.create({
          model: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
          messages: [{ role: "user", content: prompt }],
          response_format: { type: "json_object" },
          temperature: 0.9
        });

        const variation = JSON.parse(response.choices[0].message.content);
        variations.push({
          ...variation,
          title: this.validateAndTruncate(variation.title, 100),
          description: this.validateAndTruncate(variation.description, 500),
          hashtags: this.cleanHashtags(variation.hashtags),
          cta: this.validateAndTruncate(variation.cta, 100)
        });
      } catch (error) {
        console.error(`Error generating variation ${i}:`, error);
      }
    }

    return variations;
  }

  // Optimize content for specific platform
  optimizeForPlatform(content, platform) {
    const optimizations = {
      instagram: {
        maxHashtags: 10,
        preferredLength: 300,
        style: 'visual-first'
      },
      tiktok: {
        maxHashtags: 6,
        preferredLength: 150,
        style: 'trend-based'
      },
      youtube: {
        maxHashtags: 8,
        preferredLength: 500,
        style: 'informative'
      },
      reddit: {
        maxHashtags: 0,
        preferredLength: 400,
        style: 'conversational'
      }
    };

    const platformConfig = optimizations[platform] || optimizations.instagram;
    
    return {
      ...content,
      hashtags: platform === 'reddit' ? '' : content.hashtags.split(' ').slice(0, platformConfig.maxHashtags).join(' '),
      description: content.description.substring(0, platformConfig.preferredLength)
    };
  }
}

export default AIContentGeneratorService;