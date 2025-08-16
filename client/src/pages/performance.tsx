import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Brain, TrendingUp, Target, Lightbulb, Play, RefreshCw } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface PredictionResult {
  success: boolean;
  data: {
    predicted_engagement: number;
    confidence: number;
    recommendations: string[];
    model_info: {
      platform: string;
      model_type: string;
      trained_at: string;
      training_samples: number;
    };
  };
}

interface AIStatus {
  success: boolean;
  data: {
    models_available: string[];
    total_models: number;
    model_details: Record<string, any>;
  };
}

export default function Performance() {
  const [predictionForm, setPredictionForm] = useState({
    asset_id: "27",
    platform: "youtube",
    title: "",
    description: "",
    hashtags: "",
    language: "en"
  });

  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: aiStatus } = useQuery<AIStatus>({
    queryKey: ["/api/ai/models/status"],
    refetchInterval: 30000
  });

  const { data: assetsData } = useQuery({
    queryKey: ["/api/assets"],
  });

  const trainModelMutation = useMutation({
    mutationFn: async (platform?: string) => {
      const url = platform ? `/api/ai/models/train?platform=${platform}` : "/api/ai/models/train";
      const response = await fetch(url, { method: "POST" });
      return response.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast({
          title: "Training Started",
          description: data.message || "AI models are being trained"
        });
      } else {
        toast({
          title: "Training Info",
          description: data.error || "Insufficient training data - need more posts with metrics",
          variant: "default"
        });
      }
      queryClient.invalidateQueries({ queryKey: ["/api/ai/models/status"] });
    },
    onError: (error: any) => {
      console.error('Training error:', error);
      toast({
        title: "Training Failed", 
        description: error?.message || "Could not start model training",
        variant: "destructive"
      });
    }
  });

  const predictMutation = useMutation({
    mutationFn: async (formData: typeof predictionForm) => {
      const response = await fetch("/api/ai/predict/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      return response.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast({
          title: "Prediction Complete",
          description: `Predicted engagement: ${(data.data.predicted_engagement * 100).toFixed(1)}%`
        });
      }
    }
  });

  const handlePredict = () => {
    if (!predictionForm.title) {
      toast({
        title: "Missing Title",
        description: "Please enter a title for prediction",
        variant: "destructive"
      });
      return;
    }
    predictMutation.mutate(predictionForm);
  };

  const predictionResult = predictMutation.data as PredictionResult | undefined;

  return (
    <div className="space-y-6 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300 p-4 md:p-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between space-y-4 md:space-y-0">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-gray-900 dark:text-white">AI Performance Prediction</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base">
            Predict content performance before publishing with machine learning
          </p>
        </div>
      </div>

      {/* AI Models Status */}
      <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-2 text-gray-900 dark:text-white">
              <Brain className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <span>AI Models Status</span>
            </div>
            <Button
              onClick={() => trainModelMutation.mutate({})}
              disabled={trainModelMutation.isPending}
              size="sm"
              data-testid="button-train-models"
            >
              {trainModelMutation.isPending ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              Train All Models
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(aiStatus as any)?.data?.total_models > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(aiStatus as any)?.data?.models_available?.map((platform: string) => {
                const model = (aiStatus as any)?.data?.model_details?.[platform];
                return (
                  <div key={platform} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium capitalize">{platform}</h4>
                      <Badge variant="outline" className="text-green-600">
                        Ready
                      </Badge>
                    </div>
                    <div className="space-y-2">
                      <div className="text-sm text-muted-foreground">
                        {model?.model_type} • {model?.training_samples} samples
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Accuracy</span>
                        <span className="text-sm font-medium">
                          {((model?.r2_score || 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={(model?.r2_score || 0) * 100} className="h-2" />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => trainModelMutation.mutate({ platform })}
                        disabled={trainModelMutation.isPending}
                        className="w-full"
                      >
                        Retrain
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8">
              <Brain className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">No AI Models Trained</h3>
              <p className="text-muted-foreground mb-4">
                Train models with historical data to start making predictions
              </p>
              <Button
                onClick={() => trainModelMutation.mutate({})}
                disabled={trainModelMutation.isPending}
                data-testid="button-initial-train"
              >
                {trainModelMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                Start Training
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Performance Prediction Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Target className="w-5 h-5" />
            <span>Predict Content Performance</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="asset_id">Asset ID</Label>
                  <Input
                    id="asset_id"
                    value={predictionForm.asset_id}
                    onChange={(e) => setPredictionForm(prev => ({ ...prev, asset_id: e.target.value }))}
                    placeholder="27"
                    data-testid="input-asset-id"
                  />
                </div>
                <div>
                  <Label htmlFor="platform">Platform</Label>
                  <Select
                    value={predictionForm.platform}
                    onValueChange={(value) => setPredictionForm(prev => ({ ...prev, platform: value }))}
                  >
                    <SelectTrigger data-testid="select-platform">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="youtube">YouTube</SelectItem>
                      <SelectItem value="instagram">Instagram</SelectItem>
                      <SelectItem value="tiktok">TikTok</SelectItem>
                      <SelectItem value="reddit">Reddit</SelectItem>
                      <SelectItem value="pinterest">Pinterest</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={predictionForm.title}
                  onChange={(e) => setPredictionForm(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="Enter engaging title for your content"
                  data-testid="input-title"
                />
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={predictionForm.description}
                  onChange={(e) => setPredictionForm(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe your content..."
                  rows={3}
                  data-testid="textarea-description"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="hashtags">Hashtags</Label>
                  <Input
                    id="hashtags"
                    value={predictionForm.hashtags}
                    onChange={(e) => setPredictionForm(prev => ({ ...prev, hashtags: e.target.value }))}
                    placeholder="#tech,#AI,#innovation"
                    data-testid="input-hashtags"
                  />
                </div>
                <div>
                  <Label htmlFor="language">Language</Label>
                  <Select
                    value={predictionForm.language}
                    onValueChange={(value) => setPredictionForm(prev => ({ ...prev, language: value }))}
                  >
                    <SelectTrigger data-testid="select-language">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button
                onClick={handlePredict}
                disabled={predictMutation.isPending || !predictionForm.title}
                className="w-full"
                data-testid="button-predict"
              >
                {predictMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <TrendingUp className="w-4 h-4 mr-2" />
                )}
                Predict Performance
              </Button>
            </div>

            {/* Prediction Results */}
            <div className="space-y-4">
              {predictionResult?.success ? (
                <>
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">Prediction Results</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Predicted Engagement</span>
                          <span className="text-2xl font-bold text-blue-600" data-testid="text-engagement-rate">
                            {(predictionResult.data.predicted_engagement * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress 
                          value={predictionResult.data.predicted_engagement * 100} 
                          className="h-3"
                        />
                      </div>

                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium">Confidence</span>
                          <span className="text-lg font-semibold text-green-600" data-testid="text-confidence">
                            {(predictionResult.data.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        <Progress 
                          value={predictionResult.data.confidence * 100} 
                          className="h-2"
                        />
                      </div>

                      <div className="text-sm text-muted-foreground">
                        <strong>Model:</strong> {predictionResult.data.model_info.model_type}<br />
                        <strong>Platform:</strong> {predictionResult.data.model_info.platform}<br />
                        <strong>Training samples:</strong> {predictionResult.data.model_info.training_samples}
                      </div>
                    </CardContent>
                  </Card>

                  {predictionResult.data.recommendations.length > 0 && (
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                          <Lightbulb className="w-5 h-5" />
                          <span>AI Recommendations</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2" data-testid="list-recommendations">
                          {predictionResult.data.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start space-x-2">
                              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                              <span className="text-sm">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : predictionResult && !predictionResult.success ? (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center text-muted-foreground">
                      <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Prediction failed: {JSON.stringify(predictionResult) || "No model available"}</p>
                      <p className="text-sm mt-2">Try training models first or check your inputs</p>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-center text-muted-foreground">
                      <TrendingUp className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Enter content details and click "Predict Performance" to see AI predictions</p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}