import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Upload, Wand2, CheckCircle, AlertTriangle, Image, Video, FileText } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";

interface AIGeneratedContent {
  title: string;
  description: string;
  hashtags: string;
  cta: string;
  compliance_score: number;
  flagged_issues: string[];
  approved: boolean;
}

interface SimpleByopUploaderProps {
  onSubmissionComplete?: (submissionId: string) => void;
}

export function SimpleByopUploader({ onSubmissionComplete }: SimpleByopUploaderProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [userMessage, setUserMessage] = useState("");
  const [aiContent, setAiContent] = useState<AIGeneratedContent | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Generate AI content from files and user message
  const generateContentMutation = useMutation({
    mutationFn: async ({ files, message }: { files: File[], message: string }) => {
      const formData = new FormData();
      files.forEach((file, index) => {
        formData.append(`file_${index}`, file);
      });
      formData.append('user_message', message);
      formData.append('generate_content', 'true');

      const response = await fetch('/api/byop/ai-generate', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la génération de contenu');
      }

      return response.json();
    },
    onSuccess: (data: AIGeneratedContent) => {
      setAiContent(data);
      if (!data.approved) {
        toast({
          title: "Contenu signalé",
          description: "Ce contenu nécessite une révision avant publication",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Contenu généré",
          description: "L'IA a créé votre post automatiquement",
        });
      }
    },
    onError: (error) => {
      toast({
        title: "Erreur",
        description: "Impossible de générer le contenu",
        variant: "destructive",
      });
    }
  });

  // Submit final content
  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!aiContent) throw new Error('Pas de contenu généré');

      return apiRequest("POST", "/api/byop/submit-simple", {
        title: aiContent.title,
        description: aiContent.description,
        hashtags: aiContent.hashtags,
        cta: aiContent.cta,
        files: selectedFiles.map(f => f.name),
        compliance_score: aiContent.compliance_score,
        user_message: userMessage
      });
    },
    onSuccess: (data) => {
      toast({
        title: "Post soumis",
        description: "Votre contenu sera publié après validation",
      });
      
      // Reset form
      setSelectedFiles([]);
      setUserMessage("");
      setAiContent(null);
      
      queryClient.invalidateQueries({ queryKey: ["/api/byop/submissions"] });
      onSubmissionComplete?.(data.submission_id);
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible de soumettre le post",
        variant: "destructive",
      });
    }
  });

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const validFiles = files.filter(file => {
      const isImage = file.type.startsWith('image/');
      const isVideo = file.type.startsWith('video/');
      const isValid = isImage || isVideo;
      const isSize = file.size <= 50 * 1024 * 1024; // 50MB max
      
      if (!isValid) {
        toast({
          title: "Fichier non supporté",
          description: `${file.name} n'est pas une image ou vidéo`,
          variant: "destructive",
        });
      } else if (!isSize) {
        toast({
          title: "Fichier trop volumineux",
          description: `${file.name} dépasse 50MB`,
          variant: "destructive",
        });
      }
      
      return isValid && isSize;
    });

    setSelectedFiles(prev => [...prev, ...validFiles].slice(0, 3)); // Max 3 files
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleGenerateContent = () => {
    if (selectedFiles.length === 0) {
      toast({
        title: "Fichiers requis",
        description: "Ajoutez au moins une photo ou vidéo",
        variant: "destructive",
      });
      return;
    }

    setIsProcessing(true);
    generateContentMutation.mutate({ 
      files: selectedFiles, 
      message: userMessage 
    });
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (file.type.startsWith('video/')) return <Video className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const getComplianceColor = (score: number) => {
    if (score >= 90) return "text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300";
    if (score >= 70) return "text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300";
    return "text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300";
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            1. Ajoutez vos fichiers
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="file-upload" className="text-sm font-medium">
              Photos ou vidéos (max 3 fichiers, 50MB chacun)
            </Label>
            <Input
              id="file-upload"
              type="file"
              multiple
              accept="image/*,video/*"
              onChange={handleFileSelect}
              className="mt-1"
              data-testid="input-file-upload"
            />
          </div>

          {selectedFiles.length > 0 && (
            <div className="space-y-2">
              <Label>Fichiers sélectionnés:</Label>
              {selectedFiles.map((file, index) => (
                <div key={index} className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  {getFileIcon(file)}
                  <span className="flex-1 text-sm truncate">{file.name}</span>
                  <span className="text-xs text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(1)}MB
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    data-testid={`button-remove-file-${index}`}
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          )}

          <div>
            <Label htmlFor="user-message">
              Message (optionnel) - Dites-nous ce que vous voulez partager
            </Label>
            <Textarea
              id="user-message"
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              placeholder="Ex: J'ai découvert ce super restaurant... ou Mes vacances à Paris..."
              className="mt-1"
              data-testid="textarea-user-message"
            />
          </div>

          <Button
            onClick={handleGenerateContent}
            disabled={selectedFiles.length === 0 || generateContentMutation.isPending}
            className="w-full"
            data-testid="button-generate-content"
          >
            <Wand2 className="w-4 h-4 mr-2" />
            {generateContentMutation.isPending ? "Génération en cours..." : "Créer mon post avec l'IA"}
          </Button>
        </CardContent>
      </Card>

      {/* AI Generated Content Review */}
      {aiContent && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wand2 className="w-5 h-5" />
              2. Contenu généré par l'IA
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4">
              <div>
                <Label className="text-sm font-medium">Titre</Label>
                <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  {aiContent.title}
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium">Description</Label>
                <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  {aiContent.description}
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium">Hashtags</Label>
                <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  {aiContent.hashtags}
                </div>
              </div>

              <div>
                <Label className="text-sm font-medium">Call-to-Action</Label>
                <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded">
                  {aiContent.cta}
                </div>
              </div>

              {/* Compliance Status */}
              <div className="flex items-center gap-2">
                <Label className="text-sm font-medium">Statut de conformité:</Label>
                <Badge className={getComplianceColor(aiContent.compliance_score)}>
                  {aiContent.approved ? (
                    <><CheckCircle className="w-3 h-3 mr-1" />Approuvé ({aiContent.compliance_score}%)</>
                  ) : (
                    <><AlertTriangle className="w-3 h-3 mr-1" />Signalé ({aiContent.compliance_score}%)</>
                  )}
                </Badge>
              </div>

              {aiContent.flagged_issues.length > 0 && (
                <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded">
                  <p className="text-sm font-medium text-red-800 dark:text-red-300 mb-2">
                    Problèmes détectés:
                  </p>
                  <ul className="text-sm text-red-700 dark:text-red-400 space-y-1">
                    {aiContent.flagged_issues.map((issue, index) => (
                      <li key={index}>• {issue}</li>
                    ))}
                  </ul>
                </div>
              )}

              <Button
                onClick={() => submitMutation.mutate()}
                disabled={!aiContent.approved || submitMutation.isPending}
                className="w-full"
                data-testid="button-submit-post"
              >
                {submitMutation.isPending ? "Soumission..." : "Publier mon post"}
              </Button>

              {!aiContent.approved && (
                <p className="text-sm text-red-600 dark:text-red-400 text-center">
                  Ce contenu nécessite une révision manuelle avant publication
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}