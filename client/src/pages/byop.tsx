import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { ByopPublishButton } from "@/components/ByopPublishButton";
import { SimpleByopUploader } from "@/components/SimpleByopUploader";
import { 
  Plus, 
  Share2, 
  Copy, 
  Send, 
  MessageCircle, 
  Twitter, 
  Facebook,
  Mail,
  ExternalLink,
  CheckCircle,
  Clock,
  AlertCircle,
  Users
} from "lucide-react";

interface ByopConfig {
  enabled: boolean;
  share_email_enabled: boolean;
  share_email_daily_limit: number;
  default_hashtags: string;
}

interface ByopSubmission {
  id: string;
  partner_id: string;
  title: string;
  description: string;
  hashtags: string;
  cta: string;
  status: 'submitted' | 'processing' | 'ready' | 'failed';
  created_at: string;
}

interface ShareKit {
  submission: ByopSubmission;
  short_url: string;
  share_text: string;
  share_intents: {
    whatsapp: string;
    telegram: string;
    twitter: string;
    facebook: string;
    copy: string;
  };
}

export default function ByopPage() {
  const [activeTab, setActiveTab] = useState("create");
  const [selectedSubmission, setSelectedSubmission] = useState<string | null>(null);
  const [emailList, setEmailList] = useState("");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Check device verification from cookie with better error handling
  const isDeviceVerified = () => {
    try {
      if (typeof window !== 'undefined' && typeof document !== 'undefined') {
        const cookies = document.cookie || '';
        console.log('Device verification check - cookies:', cookies);
        return cookies.includes('device_verified=true');
      }
    } catch (error) {
      console.error('Error checking device verification:', error);
    }
    return false;
  };

  // Queries
  const { data: config } = useQuery<ByopConfig>({
    queryKey: ["/api/byop/config"],
  });

  const { data: submissions } = useQuery<{ success: boolean; data: ByopSubmission[] }>({
    queryKey: ["/api/byop/submissions"],
    enabled: config?.enabled
  });

  const { data: shareKit } = useQuery<{ success: boolean; data: ShareKit }>({
    queryKey: ["/api/byop/share-kit", selectedSubmission],
    enabled: !!selectedSubmission
  });

  // Mutations
  const createSubmissionMutation = useMutation({
    mutationFn: async (formData: {
      source_url: string;
      title: string;
      description: string;
      hashtags: string;
      cta: string;
    }) => {
      const response = await fetch("/api/byop/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      return response.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast({
          title: "Contenu créé !",
          description: "Votre contenu BYOP a été créé avec succès"
        });
        queryClient.invalidateQueries({ queryKey: ["/api/byop/submissions"] });
        setActiveTab("manage");
      }
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible de créer le contenu",
        variant: "destructive"
      });
    }
  });

  const logShareMutation = useMutation({
    mutationFn: async ({ channel, recipients = 0, message = "" }: {
      channel: string;
      recipients?: number;
      message?: string;
    }) => {
      const response = await fetch("/api/byop/log-share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel, recipients_count: recipients, message })
      });
      return response.json();
    }
  });

  const emailShareMutation = useMutation({
    mutationFn: async ({ submissionId, emails }: { submissionId: string; emails: string }) => {
      const response = await fetch("/api/byop/email-share", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ submission_id: submissionId, emails })
      });
      return response.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast({
          title: "Emails envoyés !",
          description: `${data.sent_count} emails envoyés avec succès`
        });
        setEmailList("");
      }
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible d'envoyer les emails",
        variant: "destructive"
      });
    }
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    createSubmissionMutation.mutate({
      source_url: formData.get("source_url") as string,
      title: formData.get("title") as string,
      description: formData.get("description") as string,
      hashtags: formData.get("hashtags") as string,
      cta: formData.get("cta") as string,
    });
  };

  const handleCopyText = async () => {
    if (shareKit?.data?.share_text) {
      await navigator.clipboard.writeText(shareKit.data.share_text);
      logShareMutation.mutate({ channel: "copy" });
      toast({
        title: "Copié !",
        description: "Le texte a été copié dans le presse-papiers"
      });
    }
  };

  const handleSocialShare = (platform: string, url: string) => {
    window.open(url, '_blank');
    logShareMutation.mutate({ channel: platform });
  };

  const handleEmailShare = () => {
    if (!selectedSubmission || !emailList.trim()) {
      toast({
        title: "Erreur",
        description: "Veuillez sélectionner un contenu et saisir des emails",
        variant: "destructive"
      });
      return;
    }

    emailShareMutation.mutate({
      submissionId: selectedSubmission,
      emails: emailList
    });
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "ready":
        return <Badge className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300"><CheckCircle className="w-3 h-3 mr-1" />Prêt</Badge>;
      case "processing":
        return <Badge className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300"><Clock className="w-3 h-3 mr-1" />En cours</Badge>;
      case "failed":
        return <Badge className="bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-300"><AlertCircle className="w-3 h-3 mr-1" />Échec</Badge>;
      default:
        return <Badge variant="outline"><Clock className="w-3 h-3 mr-1" />Soumis</Badge>;
    }
  };

  // Check authentication with real-time cookie refresh
  const [authState, setAuthState] = useState(() => {
    if (typeof window === 'undefined' || typeof document === 'undefined') return false;
    const cookies = document.cookie || '';
    return cookies.includes('partner_id=') && cookies.includes('device_verified=true');
  });

  // Recheck authentication on mount and periodically
  useEffect(() => {
    const checkAuth = () => {
      if (typeof window === 'undefined' || typeof document === 'undefined') return false;
      
      const cookies = document.cookie || '';
      const hasPartnerId = cookies.includes('partner_id=');
      const hasDeviceVerified = cookies.includes('device_verified=true');
      
      const partnerIdMatch = cookies.match(/partner_id=([^;]+)/);
      const partnerId = partnerIdMatch ? partnerIdMatch[1] : null;
      
      console.log('BYOP Real-time Auth check:', { 
        hasPartnerId, 
        hasDeviceVerified, 
        partnerId,
        cookieLength: cookies.length,
        fullCookies: cookies,
        timestamp: new Date().toISOString()
      });
      
      const authenticated = hasPartnerId && hasDeviceVerified;
      setAuthState(authenticated);
      return authenticated;
    };

    // Check immediately
    checkAuth();
    
    // Check every 2 seconds to catch cookie changes
    const interval = setInterval(checkAuth, 2000);
    
    return () => clearInterval(interval);
  }, []);

  const isAuthenticated = authState;

  if (!config?.enabled) {
    return (
      <div className="space-y-6 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300 p-4 md:p-6">
        <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <CardContent className="pt-6">
            <div className="text-center">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                BYOP non disponible
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                La fonctionnalité "Bring Your Own Post" n'est pas activée sur cette instance.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="space-y-6 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300 p-4 md:p-6">
        <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 max-w-md mx-auto">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Connexion requise
              </h2>
              <p className="text-gray-600 dark:text-gray-400">
                Connectez-vous à votre espace partenaire pour accéder à BYOP et suivre vos gains.
              </p>
              <div className="space-y-2">
                <Button 
                  onClick={() => window.location.href = '/partner-auth'}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  data-testid="button-partner-login"
                >
                  Se connecter
                </Button>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Authentification par magic-link sécurisé
                </p>
                <div className="mt-4 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                  Debug: Cookies = {typeof document !== 'undefined' ? document.cookie : 'N/A'}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300 p-4 md:p-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between space-y-4 md:space-y-0">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">💰 BYOP - Créer du Contenu Viral</h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base">
            Uploadez vos photos/vidéos, l'IA crée un post viral automatiquement
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <Button 
            variant="outline"
            onClick={() => window.location.href = '/partner-profile'}
            className="bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700"
            data-testid="button-partner-profile"
          >
            <Users className="w-4 h-4 mr-2" />
            Mon profil
          </Button>
          <Badge variant="outline" className="bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-700">
            <Plus className="w-4 h-4 mr-2" />
            Créateur de contenu
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3 bg-white dark:bg-gray-800">
          <TabsTrigger value="create" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
            <Plus className="w-4 h-4 mr-2" />
            Créer
          </TabsTrigger>
          <TabsTrigger value="manage" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
            <Share2 className="w-4 h-4 mr-2" />
            Gérer
          </TabsTrigger>
          <TabsTrigger value="share" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
            <Send className="w-4 h-4 mr-2" />
            Partager
          </TabsTrigger>
        </TabsList>

        <TabsContent value="create">
          <SimpleByopUploader 
            onSubmissionComplete={(submissionId) => {
              toast({
                title: "Post créé avec l'IA",
                description: "Votre contenu a été généré et soumis automatiquement"
              });
              queryClient.invalidateQueries({ queryKey: ["/api/byop/submissions"] });
              setActiveTab("manage");
            }}
          />
        </TabsContent>

        <TabsContent value="manage">
          <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
            <CardHeader>
              <CardTitle className="text-gray-900 dark:text-white">Mes contenus BYOP</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                Gérez vos contenus créés et leur statut
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {submissions?.data?.map((submission) => (
                  <div
                    key={submission.id}
                    className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedSubmission === submission.id
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                        : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                    }`}
                    onClick={() => setSelectedSubmission(submission.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 dark:text-white">{submission.title}</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{submission.description}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-500 mt-2">
                          Créé le {new Date(submission.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="ml-4">
                        {getStatusBadge(submission.status)}
                      </div>
                    </div>
                  </div>
                ))}
                
                {(!submissions?.data || submissions.data.length === 0) && (
                  <div className="text-center py-8">
                    <p className="text-gray-500 dark:text-gray-400">Aucun contenu créé pour le moment</p>
                    <Button
                      variant="outline"
                      onClick={() => setActiveTab("create")}
                      className="mt-4"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Créer mon premier contenu
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="share">
          {!selectedSubmission ? (
            <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
              <CardContent className="pt-6">
                <div className="text-center">
                  <Share2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Sélectionnez un contenu à partager
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    Choisissez un contenu dans l'onglet "Gérer" pour accéder aux outils de partage
                  </p>
                  <Button variant="outline" onClick={() => setActiveTab("manage")}>
                    Voir mes contenus
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
                <CardHeader>
                  <CardTitle className="text-gray-900 dark:text-white">Kit de partage</CardTitle>
                  <CardDescription className="text-gray-600 dark:text-gray-400">
                    Tous les outils pour partager votre contenu
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {shareKit?.data && (
                    <>
                      <div>
                        <Label className="text-gray-900 dark:text-white">Lien court</Label>
                        <div className="flex mt-2">
                          <Input
                            value={shareKit.data.short_url}
                            readOnly
                            className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                          />
                          <Button
                            variant="outline"
                            className="ml-2"
                            onClick={() => navigator.clipboard.writeText(shareKit.data.short_url)}
                          >
                            <Copy className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>

                      <div>
                        <Label className="text-gray-900 dark:text-white">Texte de partage</Label>
                        <Textarea
                          value={shareKit.data.share_text}
                          readOnly
                          rows={4}
                          className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                        />
                        <Button
                          variant="outline"
                          className="mt-2"
                          onClick={handleCopyText}
                        >
                          <Copy className="w-4 h-4 mr-2" />
                          Copier le texte
                        </Button>
                      </div>

                      <div>
                        <Label className="text-gray-900 dark:text-white">Partage sur les réseaux sociaux</Label>
                        <div className="flex flex-wrap gap-2 mt-2">
                          <Button
                            variant="outline"
                            onClick={() => handleSocialShare("whatsapp", shareKit.data.share_intents.whatsapp)}
                            className="bg-green-50 hover:bg-green-100 text-green-700 border-green-200"
                          >
                            <MessageCircle className="w-4 h-4 mr-2" />
                            WhatsApp
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleSocialShare("telegram", shareKit.data.share_intents.telegram)}
                            className="bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200"
                          >
                            <Send className="w-4 h-4 mr-2" />
                            Telegram
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleSocialShare("twitter", shareKit.data.share_intents.twitter)}
                            className="bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200"
                          >
                            <Twitter className="w-4 h-4 mr-2" />
                            Twitter
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleSocialShare("facebook", shareKit.data.share_intents.facebook)}
                            className="bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-200"
                          >
                            <Facebook className="w-4 h-4 mr-2" />
                            Facebook
                          </Button>
                        </div>
                      </div>

                      {config?.share_email_enabled && (
                        <div>
                          <Label className="text-gray-900 dark:text-white">Partage par email</Label>
                          <Textarea
                            value={emailList}
                            onChange={(e) => setEmailList(e.target.value)}
                            placeholder="email1@example.com, email2@example.com"
                            rows={3}
                            className="mt-2 bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                          />
                          <div className="flex justify-between items-center mt-2">
                            <Button
                              onClick={handleEmailShare}
                              disabled={emailShareMutation.isPending || !emailList.trim()}
                              className="bg-blue-600 hover:bg-blue-700"
                            >
                              <Mail className="w-4 h-4 mr-2" />
                              {emailShareMutation.isPending ? "Envoi..." : "Envoyer"}
                            </Button>
                            <span className="text-xs text-gray-500 dark:text-gray-400">
                              Limite: {config?.share_email_daily_limit || 200}/jour
                            </span>
                          </div>
                        </div>
                      )}

                      {/* BYOP Publishing Button */}
                      <ByopPublishButton 
                        submissionId={selectedSubmission}
                        disabled={!selectedSubmission}
                      />
                    </>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}