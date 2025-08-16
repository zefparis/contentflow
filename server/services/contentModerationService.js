// Content Moderation Service
// Uses OpenAI to analyze content for compliance and safety

import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

class ContentModerationService {
  
  async analyzeContent(text, files = []) {
    try {
      const results = await Promise.all([
        this.analyzeText(text),
        files.length > 0 ? this.analyzeFiles(files) : Promise.resolve({ approved: true, issues: [] })
      ]);

      const textResult = results[0];
      const fileResult = results[1];

      const combinedScore = Math.min(textResult.score, fileResult.score || 100);
      const allIssues = [...textResult.issues, ...(fileResult.issues || [])];

      return {
        approved: combinedScore >= 70 && allIssues.length === 0,
        score: combinedScore,
        issues: allIssues,
        details: {
          text: textResult,
          files: fileResult
        }
      };
    } catch (error) {
      console.error('Content moderation error:', error);
      // Conservative approach: reject on error
      return {
        approved: false,
        score: 0,
        issues: ['Erreur technique lors de la modération'],
        details: { error: error.message }
      };
    }
  }

  async analyzeText(text) {
    if (!text || text.trim().length === 0) {
      return { approved: true, score: 100, issues: [] };
    }

    const prompt = `Analyse ce contenu pour détecter:
1. Discours de haine ou discrimination
2. Contenu violent ou choquant
3. Spam ou contenu trompeur
4. Contenu sexuellement explicite
5. Violations de droits d'auteur
6. Désinformation

Contenu à analyser: "${text}"

Réponds uniquement avec un JSON dans ce format:
{
  "score": number (0-100, 100 = complètement sûr),
  "approved": boolean,
  "issues": ["liste des problèmes détectés"],
  "category": "safe|questionable|unsafe"
}`;

    try {
      const response = await openai.chat.completions.create({
        model: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
        messages: [
          {
            role: "system",
            content: "Tu es un modérateur de contenu expert. Analyse le contenu de manière stricte mais équitable."
          },
          {
            role: "user",
            content: prompt
          }
        ],
        response_format: { type: "json_object" },
        temperature: 0.1
      });

      const result = JSON.parse(response.choices[0].message.content);
      
      return {
        approved: result.approved && result.score >= 70,
        score: result.score,
        issues: result.issues || [],
        category: result.category
      };
    } catch (error) {
      console.error('Text analysis error:', error);
      return {
        approved: false,
        score: 0,
        issues: ['Erreur lors de l\'analyse du texte'],
        category: 'unsafe'
      };
    }
  }

  async analyzeFiles(files) {
    // Pour l'instant, analyse basique des noms de fichiers
    // À améliorer avec analyse d'images OpenAI Vision
    const issues = [];
    let minScore = 100;

    for (const file of files) {
      const fileSize = file.size || 0;
      const fileName = (file.originalname || file.name || 'upload').toLowerCase();
      
      if (fileSize > 50 * 1024 * 1024) { // 50MB
        issues.push(`Fichier trop volumineux: ${fileName}`);
        minScore = Math.min(minScore, 40);
      }
      const suspiciousWords = [
        'porn', 'nude', 'xxx', 'sex', 'adult', 'nsfw',
        'hate', 'nazi', 'terror', 'violence', 'gore',
        'spam', 'scam', 'phishing', 'malware'
      ];

      for (const word of suspiciousWords) {
        if (fileName.includes(word)) {
          issues.push(`Nom de fichier suspect: ${fileName}`);
          minScore = Math.min(minScore, 30);
          break;
        }
      }

      // Check file type
      const fileType = file.mimetype || file.type || '';
      if (!fileType.startsWith('image/') && !fileType.startsWith('video/')) {
        issues.push(`Type de fichier non autorisé: ${fileName}`);
        minScore = Math.min(minScore, 20);
      }
    }

    return {
      approved: issues.length === 0 && minScore >= 70,
      score: minScore,
      issues
    };
  }

  async analyzeImageWithVision(imageBuffer) {
    try {
      const base64Image = imageBuffer.toString('base64');
      
      const response = await openai.chat.completions.create({
        model: "gpt-4o", // the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
        messages: [
          {
            role: "user",
            content: [
              {
                type: "text",
                text: `Analyse cette image pour détecter du contenu inapproprié:
- Nudité ou contenu sexuel explicite
- Violence ou contenu choquant  
- Discours de haine ou symboles offensants
- Contenu illégal ou dangereux

Réponds avec un JSON:
{
  "approved": boolean,
  "score": number (0-100),
  "issues": ["liste des problèmes"],
  "description": "description courte de l'image"
}`
              },
              {
                type: "image_url",
                image_url: {
                  url: `data:image/jpeg;base64,${base64Image}`
                }
              }
            ],
          },
        ],
        response_format: { type: "json_object" },
        max_tokens: 500,
      });

      return JSON.parse(response.choices[0].message.content);
    } catch (error) {
      console.error('Vision analysis error:', error);
      return {
        approved: false,
        score: 0,
        issues: ['Erreur lors de l\'analyse d\'image'],
        description: 'Analyse impossible'
      };
    }
  }

  // Generate content score for trending/performance prediction
  getContentQualityScore(content) {
    let score = 50; // Base score

    // Length optimization
    if (content.title && content.title.length > 10 && content.title.length < 100) score += 10;
    if (content.description && content.description.length > 50 && content.description.length < 500) score += 10;
    
    // Hashtag count
    const hashtagCount = (content.hashtags.match(/#/g) || []).length;
    if (hashtagCount >= 3 && hashtagCount <= 8) score += 10;
    
    // Call-to-action presence
    if (content.cta && content.cta.length > 0) score += 15;
    
    // Engagement potential words
    const engagementWords = ['comment', 'like', 'share', 'follow', 'subscribe', 'tag', 'mention'];
    const hasEngagement = engagementWords.some(word => 
      content.description.toLowerCase().includes(word) || 
      content.cta.toLowerCase().includes(word)
    );
    if (hasEngagement) score += 15;

    return Math.min(100, score);
  }
}

export default ContentModerationService;