// Test script for AI content generation
import AIContentGeneratorService from './aiContentGenerator.js';

async function testAIGeneration() {
  try {
    const aiGenerator = new AIContentGeneratorService();
    
    // Simulate uploaded files
    const mockFiles = [
      {
        originalname: 'photo-vacances.jpg',
        mimetype: 'image/jpeg',
        size: 1024 * 1024 * 2 // 2MB
      }
    ];
    
    const userMessage = "Mes vacances à Paris étaient incroyables !";
    
    console.log("Testing AI content generation...");
    const result = await aiGenerator.generateContent(mockFiles, userMessage);
    
    console.log("Generated content:", JSON.stringify(result, null, 2));
    
  } catch (error) {
    console.error("Test failed:", error);
  }
}

// Run test if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testAIGeneration();
}

export default testAIGeneration;