import { autoCloseStaleTickets } from "./supportBot";
import { sweepClickVelocity, recordMetricEvent } from "./riskBot";

// Configuration for automated jobs
export const SCHEDULER_CONFIG = {
  SUPPORT_AUTO_CLOSE_HOURS: 6,
  RISK_SWEEP_MINUTES: 10,
  CLEANUP_HOURS: 24
};

// Job to auto-close stale support tickets
export async function jobSupportAutoClose(): Promise<void> {
  try {
    const closedCount = await autoCloseStaleTickets();
    console.log(`🎫 Auto-closed ${closedCount} stale support tickets`);
  } catch (error) {
    console.error("❌ Error auto-closing tickets:", error);
  }
}

// Job to sweep for click velocity violations
export async function jobRiskSweep(): Promise<void> {
  try {
    const flaggedCount = await sweepClickVelocity();
    if (flaggedCount > 0) {
      console.log(`🚫 Flagged ${flaggedCount} partners for click velocity violations`);
    }
  } catch (error) {
    console.error("❌ Error in risk sweep:", error);
  }
}

// Manual trigger for testing - record test click events
export async function generateTestClickEvents(partnerId: string, count: number = 50): Promise<void> {
  console.log(`🧪 Generating ${count} test click events for partner ${partnerId}`);
  
  for (let i = 0; i < count; i++) {
    await recordMetricEvent(partnerId, "click", { 
      test: true, 
      sequence: i,
      timestamp: new Date().toISOString()
    });
    
    // Small delay to spread events over time
    if (i % 10 === 0) {
      await new Promise(resolve => setTimeout(resolve, 50));
    }
  }
  
  console.log(`✅ Generated ${count} test click events`);
}

// Simple in-memory scheduler for demonstration
class SimpleScheduler {
  private intervals: NodeJS.Timeout[] = [];
  
  start() {
    console.log("🕐 Starting ContentFlow scheduler...");
    
    // Auto-close stale tickets every 6 hours
    const supportInterval = setInterval(
      jobSupportAutoClose, 
      SCHEDULER_CONFIG.SUPPORT_AUTO_CLOSE_HOURS * 60 * 60 * 1000
    );
    
    // Risk sweep every 10 minutes
    const riskInterval = setInterval(
      jobRiskSweep, 
      SCHEDULER_CONFIG.RISK_SWEEP_MINUTES * 60 * 1000
    );
    
    this.intervals.push(supportInterval, riskInterval);
    
    // Run initial sweep after 30 seconds
    setTimeout(jobRiskSweep, 30000);
    
    console.log(`✅ Scheduler started - Support: ${SCHEDULER_CONFIG.SUPPORT_AUTO_CLOSE_HOURS}h, Risk: ${SCHEDULER_CONFIG.RISK_SWEEP_MINUTES}m`);
  }
  
  stop() {
    this.intervals.forEach(interval => clearInterval(interval));
    this.intervals = [];
    console.log("🛑 Scheduler stopped");
  }
}

export const scheduler = new SimpleScheduler();

// API endpoints for manual job triggers (testing)
export const schedulerEndpoints = {
  triggerSupportCleanup: jobSupportAutoClose,
  triggerRiskSweep: jobRiskSweep,
  generateTestEvents: generateTestClickEvents
};