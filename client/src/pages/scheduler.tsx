import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Play, Pause, Clock, CheckCircle, AlertTriangle, RefreshCw } from "lucide-react";

interface Job {
  id: number;
  kind: string;
  status: string;
  attempts: number;
  last_error: string;
  created_at: string;
}

export default function Scheduler() {
  const { data: jobsData, isLoading } = useQuery({
    queryKey: ["/api/jobs"],
    refetchInterval: 5000
  });

  const { data: statusData } = useQuery({
    queryKey: ["/api/jobs/status"],
    refetchInterval: 3000
  });

  const jobs = jobsData || [];

  const getJobStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700";
      case "running": return "bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700";
      case "queued": return "bg-yellow-50 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-700";
      case "failed": return "bg-red-50 dark:bg-red-900 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700";
      default: return "bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600";
    }
  };

  const getJobIcon = (kind: string) => {
    switch (kind) {
      case "ingest": return "📥";
      case "transform": return "🎬";
      case "publish": return "📤";
      case "metrics": return "📊";
      default: return "⚙️";
    }
  };

  const runJob = async (jobType: string) => {
    try {
      await fetch(`/api/jobs/${jobType}`, { method: "POST" });
    } catch (error: any) {
      console.error(`Failed to run ${jobType} job:`, error);
    }
  };

  const jobStats = {
    completed: (jobs as Job[])?.filter((j: Job) => j.status === "completed").length || 0,
    running: (jobs as Job[])?.filter((j: Job) => j.status === "running").length || 0,
    queued: (jobs as Job[])?.filter((j: Job) => j.status === "queued").length || 0,
    failed: (jobs as Job[])?.filter((j: Job) => j.status === "failed").length || 0,
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Scheduler</h1>
        <div className="animate-pulse space-y-4">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300 p-4 md:p-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between space-y-4 md:space-y-0">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-white">Job Scheduler</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base">
            Monitor and control automated content pipeline jobs
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
          <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700">
            Auto Mode
          </Badge>
          <Badge variant="outline" data-testid="badge-total-jobs" className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">
            {(jobs as any[])?.length || 0} Jobs
          </Badge>
        </div>
      </div>

      {/* Job Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Completed</p>
                <p className="text-2xl font-bold text-green-600" data-testid="text-completed-jobs">
                  {jobStats.completed}
                </p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Running</p>
                <p className="text-2xl font-bold text-blue-600" data-testid="text-running-jobs">
                  {jobStats.running}
                </p>
              </div>
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Queued</p>
                <p className="text-2xl font-bold text-yellow-600" data-testid="text-queued-jobs">
                  {jobStats.queued}
                </p>
              </div>
              <Clock className="w-8 h-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Failed</p>
                <p className="text-2xl font-bold text-red-600" data-testid="text-failed-jobs">
                  {jobStats.failed}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Manual Job Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Play className="w-5 h-5" />
            <span>Manual Job Control</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button 
              onClick={() => runJob("ingest")}
              className="flex flex-col items-center space-y-2 h-auto py-4"
              data-testid="button-manual-ingest"
            >
              <span className="text-2xl">📥</span>
              <span>Ingest Content</span>
              <span className="text-xs opacity-75">Fetch from sources</span>
            </Button>

            <Button 
              onClick={() => runJob("transform")}
              variant="outline"
              className="flex flex-col items-center space-y-2 h-auto py-4"
              data-testid="button-manual-transform"
            >
              <span className="text-2xl">🎬</span>
              <span>Transform Videos</span>
              <span className="text-xs opacity-75">Process with FFmpeg</span>
            </Button>

            <Button 
              onClick={() => runJob("publish")}
              variant="outline"
              className="flex flex-col items-center space-y-2 h-auto py-4"
              data-testid="button-manual-publish"
            >
              <span className="text-2xl">📤</span>
              <span>Publish Posts</span>
              <span className="text-xs opacity-75">Send to platforms</span>
            </Button>

            <Button 
              onClick={() => runJob("metrics")}
              variant="outline"
              className="flex flex-col items-center space-y-2 h-auto py-4"
              data-testid="button-manual-metrics"
            >
              <span className="text-2xl">📊</span>
              <span>Collect Metrics</span>
              <span className="text-xs opacity-75">Update analytics</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Jobs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          {!(jobs as any[])?.length ? (
            <div className="text-center py-8">
              <Clock className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Jobs Found</h3>
              <p className="text-muted-foreground">
                Jobs will appear here once they are created
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {(jobs as any[])?.slice(0, 10).map((job: Job) => (
                <div key={job.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <span className="text-2xl">{getJobIcon(job.kind)}</span>
                    <div>
                      <h4 className="font-medium capitalize" data-testid={`text-job-kind-${job.id}`}>
                        {job.kind} Job
                      </h4>
                      <p className="text-sm text-muted-foreground">
                        ID: {job.id} • Created: {new Date(job.created_at).toLocaleString()}
                      </p>
                      {job.last_error && (
                        <p className="text-sm text-red-600 mt-1" data-testid={`text-error-${job.id}`}>
                          Error: {job.last_error.slice(0, 100)}...
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {job.attempts > 1 && (
                      <Badge variant="outline" className="text-orange-600">
                        Attempt {job.attempts}
                      </Badge>
                    )}
                    <Badge 
                      variant="outline" 
                      className={getJobStatusColor(job.status)}
                      data-testid={`badge-job-status-${job.id}`}
                    >
                      {job.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pipeline Status */}
      {statusData && (
        <Card>
          <CardHeader>
            <CardTitle>Pipeline Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Overall Status</span>
                <Badge 
                  variant="outline" 
                  className="bg-green-50 text-green-700"
                  data-testid="badge-pipeline-status"
                >
                  {(statusData as any)?.pipeline_status || "Active"}
                </Badge>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span>Jobs in Queue:</span>
                  <span className="font-medium" data-testid="text-queue-size">
                    {(statusData as any)?.jobs_in_queue || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Assets Processed:</span>
                  <span className="font-medium" data-testid="text-assets-processed">
                    {(statusData as any)?.assets_processed || 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Last Ingest:</span>
                  <span className="font-medium" data-testid="text-last-ingest">
                    {(statusData as any)?.last_ingest || "Never"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Last Transform:</span>
                  <span className="font-medium" data-testid="text-last-transform">
                    {(statusData as any)?.last_transform || "Never"}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}