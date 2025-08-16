import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { 
  Upload, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  Youtube,
  Instagram,
  Twitter
} from "lucide-react";
import { apiRequest } from "@/lib/queryClient";

interface PublishResponse {
  ok: boolean;
  created: Array<{
    platform: string;
    assignment_id: string;
  }>;
  skipped: Array<{
    platform: string;
    reason: string;
  }>;
  submissionId: string;
  assetId: string;
  error?: string;
}

interface ByopPublishButtonProps {
  submissionId: string;
  disabled?: boolean;
}

const PLATFORM_ICONS = {
  youtube: Youtube,
  instagram: Instagram,
  reddit: Twitter,
  pinterest: Upload
};

const PLATFORM_LABELS = {
  youtube: "YouTube",
  instagram: "Instagram", 
  reddit: "Reddit",
  pinterest: "Pinterest"
};

export function ByopPublishButton({ submissionId, disabled = false }: ByopPublishButtonProps) {
  const [publishResult, setPublishResult] = useState<PublishResponse | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const publishMutation = useMutation({
    mutationFn: async (): Promise<PublishResponse> => {
      const response = await fetch("/api/byop/publish", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          submissionId,
          platforms: ["youtube", "pinterest", "reddit", "instagram"]
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return response.json();
    },
    onSuccess: (data: PublishResponse) => {
      setPublishResult(data);
      if (data.ok) {
        const createdCount = data.created?.length || 0;
        const skippedCount = data.skipped?.length || 0;
        
        toast({
          title: "Publication lancée",
          description: `${createdCount} plateforme(s) programmée(s), ${skippedCount} ignorée(s)`
        });
        
        // Refresh any relevant queries
        queryClient.invalidateQueries({ queryKey: ["/api/assignments"] });
        queryClient.invalidateQueries({ queryKey: ["/api/jobs"] });
      } else {
        toast({
          title: "Erreur de publication",
          description: data.error || "Erreur inconnue",
          variant: "destructive"
        });
      }
    },
    onError: (error: Error) => {
      toast({
        title: "Erreur",
        description: error.message || "Erreur lors de la publication",
        variant: "destructive"
      });
    }
  });

  const handlePublish = () => {
    setPublishResult(null);
    publishMutation.mutate();
  };

  const getReasonLabel = (reason: string) => {
    switch (reason) {
      case "no_connected_account":
        return "Compte non connecté";
      case "already_assigned":
        return "Déjà programmé";
      default:
        return reason;
    }
  };

  return (
    <div className="space-y-4 p-4 border rounded-lg bg-gray-50 dark:bg-gray-700">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-medium text-gray-900 dark:text-white">Publication directe</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Publier sur vos comptes connectés
          </p>
        </div>
        <Button
          onClick={handlePublish}
          disabled={disabled || publishMutation.isPending}
          className="bg-blue-600 hover:bg-blue-700 text-white"
          data-testid="button-publish-accounts"
        >
          {publishMutation.isPending ? (
            <>
              <Clock className="w-4 h-4 mr-2 animate-spin" />
              Publication...
            </>
          ) : (
            <>
              <Upload className="w-4 h-4 mr-2" />
              Publier sur mes comptes
            </>
          )}
        </Button>
      </div>

      {publishResult && (
        <div className="space-y-3" data-testid="publish-results">
          {publishResult.ok ? (
            <>
              {publishResult.created && publishResult.created.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-green-700 dark:text-green-300 mb-2">
                    <CheckCircle className="w-4 h-4 inline mr-1" />
                    Programmé pour publication:
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {publishResult.created.map((item, index) => {
                      const Icon = PLATFORM_ICONS[item.platform as keyof typeof PLATFORM_ICONS] || Upload;
                      const label = PLATFORM_LABELS[item.platform as keyof typeof PLATFORM_LABELS] || item.platform;
                      return (
                        <Badge 
                          key={index}
                          className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300"
                          data-testid={`badge-created-${item.platform}`}
                        >
                          <Icon className="w-3 h-3 mr-1" />
                          {label}
                        </Badge>
                      );
                    })}
                  </div>
                </div>
              )}

              {publishResult.skipped && publishResult.skipped.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-orange-700 dark:text-orange-300 mb-2">
                    <AlertCircle className="w-4 h-4 inline mr-1" />
                    Ignoré:
                  </p>
                  <div className="space-y-1">
                    {publishResult.skipped.map((item, index) => {
                      const Icon = PLATFORM_ICONS[item.platform as keyof typeof PLATFORM_ICONS] || Upload;
                      const label = PLATFORM_LABELS[item.platform as keyof typeof PLATFORM_LABELS] || item.platform;
                      return (
                        <div 
                          key={index} 
                          className="flex items-center text-sm text-orange-600 dark:text-orange-400"
                          data-testid={`skipped-${item.platform}`}
                        >
                          <Icon className="w-3 h-3 mr-2" />
                          <span className="font-medium">{label}:</span>
                          <span className="ml-1">{getReasonLabel(item.reason)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="text-sm text-red-600 dark:text-red-400" data-testid="publish-error">
              <AlertCircle className="w-4 h-4 inline mr-1" />
              {publishResult.error || "Erreur lors de la publication"}
            </div>
          )}
        </div>
      )}

      {!publishResult && !publishMutation.isPending && (
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Cette action créera des tâches de publication pour tous vos comptes connectés.
        </p>
      )}
    </div>
  );
}