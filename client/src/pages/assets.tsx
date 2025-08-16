import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Video, Clock, Globe, Tag, ExternalLink } from "lucide-react";

interface Asset {
  id: number;
  source_id: number;
  status: string;
  duration: number;
  lang: string;
  keywords: string;
  created_at: string;
  meta_json: string;
}

export default function Assets() {
  const { data: assetsData, isLoading } = useQuery({
    queryKey: ["/api/assets"],
    refetchInterval: 10000
  });

  const assets = Array.isArray(assetsData) ? assetsData : [];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ready": return "bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700";
      case "processing": return "bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700";
      case "new": return "bg-yellow-50 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-700";
      case "failed": return "bg-red-50 dark:bg-red-900 text-red-700 dark:text-red-300 border-red-200 dark:border-red-700";
      default: return "bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-600";
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold tracking-tight">Assets</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
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
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-white">Assets</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base">
            Content assets processed through the pipeline
          </p>
        </div>
        <div className="flex flex-col sm:flex-row items-start sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
          <Badge variant="outline" data-testid="badge-total-assets" className="border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300">
            {assets.length} Total
          </Badge>
          <Badge variant="outline" className="bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700">
            {assets.filter((a: Asset) => a.status === "ready").length} Ready
          </Badge>
        </div>
      </div>

      {assets.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <Video className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No Assets Found</h3>
              <p className="text-muted-foreground mb-4">
                Run the ingestion job to start processing content
              </p>
              <Button onClick={() => window.location.href = "/dashboard"}>
                Go to Dashboard
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6">
          {assets.map((asset: Asset) => {
            let metadata;
            try {
              metadata = JSON.parse(asset.meta_json || "{}");
            } catch {
              metadata = {};
            }

            const plan = metadata.plan || {};

            return (
              <Card key={asset.id} className="hover:shadow-md transition-shadow bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg text-gray-900 dark:text-white">Asset #{asset.id}</CardTitle>
                    <Badge 
                      variant="outline" 
                      className={getStatusColor(asset.status)}
                      data-testid={`badge-status-${asset.id}`}
                    >
                      {asset.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {plan.title && (
                    <div>
                      <h4 className="font-medium text-sm mb-1">Generated Title</h4>
                      <p className="text-sm text-muted-foreground" data-testid={`text-title-${asset.id}`}>
                        {plan.title}
                      </p>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center space-x-2">
                      <Clock className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm" data-testid={`text-duration-${asset.id}`}>
                        {formatDuration(asset.duration || 0)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Globe className="w-4 h-4 text-muted-foreground" />
                      <span className="text-sm uppercase" data-testid={`text-lang-${asset.id}`}>
                        {asset.lang || "en"}
                      </span>
                    </div>
                  </div>

                  {asset.keywords && (
                    <div>
                      <div className="flex items-center space-x-2 mb-2">
                        <Tag className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Keywords</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {asset.keywords.split(",").slice(0, 3).map((keyword, index) => (
                          <Badge 
                            key={index} 
                            variant="secondary" 
                            className="text-xs"
                            data-testid={`badge-keyword-${asset.id}-${index}`}
                          >
                            {keyword.trim()}
                          </Badge>
                        ))}
                        {asset.keywords.split(",").length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{asset.keywords.split(",").length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>
                  )}

                  {plan.quality_score && (
                    <div>
                      <div className="flex items-center justify-between text-sm">
                        <span>Quality Score</span>
                        <span className="font-medium" data-testid={`text-quality-${asset.id}`}>
                          {(plan.quality_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${plan.quality_score * 100}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-muted-foreground">
                    Created: {new Date(asset.created_at).toLocaleDateString()}
                  </div>

                  {metadata.source_url && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      onClick={() => window.open(metadata.source_url, '_blank')}
                      data-testid={`button-source-${asset.id}`}
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      View Source
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}