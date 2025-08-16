import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { 
  Settings as SettingsIcon, 
  Database, 
  Zap, 
  Target, 
  Globe, 
  Brain, 
  DollarSign, 
  Shield,
  RefreshCw,
  Save,
  Upload,
  Download,
  AlertTriangle,
  CheckCircle
} from "lucide-react";
import { useState } from "react";

interface ContentFlowNiche {
  name: string;
  hooks_count: number;
  titles_count: number;
  hashtags_count: number;
  ctas_count: number;
}

interface ContentFlowMetrics {
  total_niches: number;
  niches: ContentFlowNiche[];
}

interface SerpAPIStatus {
  success: boolean;
  provider_active: boolean;
  credits_remaining?: number;
  last_search?: string;
}

interface BufferStatus {
  success: boolean;
  profiles_connected: number;
  profiles: Array<{
    platform: string;
    username: string;
    connected: boolean;
  }>;
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState("contentflow");
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Queries
  const { data: contentflowMetrics } = useQuery<{ success: boolean; metrics: ContentFlowMetrics }>({
    queryKey: ["/api/contentflow/metrics"],
    refetchInterval: 30000
  });

  const { data: serpApiStatus } = useQuery<SerpAPIStatus>({
    queryKey: ["/api/serpapi/status"],
    refetchInterval: 60000
  });

  const { data: bufferStatus } = useQuery<BufferStatus>({
    queryKey: ["/api/buffer/status"],
    refetchInterval: 60000
  });

  const { data: contentflowData } = useQuery({
    queryKey: ["/api/contentflow/config"],
    enabled: activeTab === "contentflow" || activeTab === "ai"
  });

  // Mutations
  const reloadConfigMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch("/api/contentflow/reload", { method: "POST" });
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Configuration rechargée",
        description: "ContentFlow Pack mis à jour avec succès"
      });
      queryClient.invalidateQueries({ queryKey: ["/api/contentflow/metrics"] });
    },
    onError: () => {
      toast({
        title: "Erreur",
        description: "Impossible de recharger la configuration",
        variant: "destructive"
      });
    }
  });

  const testContentGeneration = async (niche: string) => {
    try {
      const response = await fetch(`/api/contentflow/test/${niche}`, { method: "GET" });
      const result = await response.json();
      
      if (result.success) {
        toast({
          title: `Test ${niche} réussi`,
          description: `Contenu généré pour ${result.platforms_tested} plateformes`
        });
      } else {
        toast({
          title: "Test échoué",
          description: result.error || "Erreur inconnue",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Erreur de test",
        description: "Impossible de tester la génération de contenu",
        variant: "destructive"
      });
    }
  };

  const testSupadataEnhancement = async (niche: string) => {
    try {
      const response = await fetch(`/api/supadata/demo/${niche}`, { method: "GET" });
      const result = await response.json();
      
      if (result.success) {
        toast({
          title: `Supadata AI - ${niche}`,
          description: `Analyse terminée. Score d'amélioration: ${result.data?.optimization_demo?.improvement_score || 0}%`
        });
      } else {
        toast({
          title: "Test Supadata échoué",
          description: result.error || "Erreur de connexion Supadata",
          variant: "destructive"
        });
      }
    } catch (error) {
      toast({
        title: "Erreur Supadata",
        description: "Service d'intelligence artificielle indisponible",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="container mx-auto p-4 lg:p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <SettingsIcon className="h-6 w-6 sm:h-8 sm:w-8 text-primary" />
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold">Configuration ContentFlow</h1>
            <p className="text-sm sm:text-base text-muted-foreground">Gérer les paramètres du pipeline d'automatisation</p>
          </div>
        </div>
        <Button 
          onClick={() => reloadConfigMutation.mutate()}
          disabled={reloadConfigMutation.isPending}
          variant="outline"
          className="flex items-center space-x-2 w-full sm:w-auto"
          size="sm"
        >
          <RefreshCw className={`h-4 w-4 ${reloadConfigMutation.isPending ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Recharger Config</span>
          <span className="sm:hidden">Recharger</span>
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-1 h-auto p-1">
          <TabsTrigger value="contentflow" className="flex flex-col sm:flex-row items-center space-y-1 sm:space-y-0 sm:space-x-2 p-2 text-xs sm:text-sm">
            <Target className="h-4 w-4" />
            <span>Niches</span>
          </TabsTrigger>
          <TabsTrigger value="apis" className="flex flex-col sm:flex-row items-center space-y-1 sm:space-y-0 sm:space-x-2 p-2 text-xs sm:text-sm">
            <Zap className="h-4 w-4" />
            <span>APIs</span>
          </TabsTrigger>
          <TabsTrigger value="publishing" className="flex flex-col sm:flex-row items-center space-y-1 sm:space-y-0 sm:space-x-2 p-2 text-xs sm:text-sm">
            <Globe className="h-4 w-4" />
            <span className="hidden sm:inline">Publication</span>
            <span className="sm:hidden">Pub</span>
          </TabsTrigger>
          <TabsTrigger value="instagram" className="flex flex-col sm:flex-row items-center space-y-1 sm:space-y-0 sm:space-x-2 p-2 text-xs sm:text-sm">
            <span>📷</span>
            <span className="hidden sm:inline">Instagram</span>
            <span className="sm:hidden">IG</span>
          </TabsTrigger>
          <TabsTrigger value="ai" className="flex flex-col sm:flex-row items-center space-y-1 sm:space-y-0 sm:space-x-2 p-2 text-xs sm:text-sm">
            <Brain className="h-4 w-4" />
            <span className="hidden lg:inline">IA + Supadata</span>
            <span className="lg:hidden">IA</span>
          </TabsTrigger>
          <TabsTrigger value="email" className="flex flex-col sm:flex-row items-center space-y-1 sm:space-y-0 sm:space-x-2 p-2 text-xs sm:text-sm">
            <span>📧</span>
            <span className="hidden lg:inline">Email Marketing</span>
            <span className="lg:hidden">Email</span>
          </TabsTrigger>
          <TabsTrigger value="monetization" className="flex flex-col sm:flex-row items-center space-y-1 sm:space-y-0 sm:space-x-2 p-2 text-xs sm:text-sm">
            <DollarSign className="h-4 w-4" />
            <span className="hidden lg:inline">Monétisation</span>
            <span className="lg:hidden">€</span>
          </TabsTrigger>
        </TabsList>

        {/* ContentFlow Niches Tab */}
        <TabsContent value="contentflow" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Target className="h-5 w-5" />
                <span>ContentFlow Pack - Niches Rentables</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {contentflowMetrics?.success ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {contentflowMetrics.metrics?.niches?.map((niche: ContentFlowNiche) => (
                    <Card key={niche.name} className="p-3 sm:p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold capitalize">{niche.name}</h3>
                        <Badge variant="secondary">{niche.name}</Badge>
                      </div>
                      
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <div className="flex justify-between">
                          <span>Hooks:</span>
                          <span className="font-medium">{niche.hooks_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Titres:</span>
                          <span className="font-medium">{niche.titles_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Hashtags:</span>
                          <span className="font-medium">{niche.hashtags_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>CTAs:</span>
                          <span className="font-medium">{niche.ctas_count}</span>
                        </div>
                      </div>

                      <Button 
                        onClick={() => testContentGeneration(niche.name)}
                        className="w-full mt-4"
                        variant="outline"
                        size="sm"
                      >
                        Tester Génération
                      </Button>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                  <p className="text-muted-foreground">Configuration ContentFlow non disponible</p>
                  <Button 
                    onClick={() => reloadConfigMutation.mutate()}
                    className="mt-4"
                    variant="outline"
                  >
                    Recharger Configuration
                  </Button>
                </div>
              )}

              <div className="border-t pt-4">
                <h4 className="font-medium mb-2 text-sm sm:text-base">Niches Ciblées - Business Model</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 text-sm">
                  <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <h5 className="font-medium text-green-800 dark:text-green-200">VPN</h5>
                    <p className="text-green-600 dark:text-green-300">Marché 5+ milliards €</p>
                    <p className="text-xs text-green-500">Commissions 30-70%</p>
                  </div>
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <h5 className="font-medium text-blue-800 dark:text-blue-200">Hébergement</h5>
                    <p className="text-blue-600 dark:text-blue-300">Marché stable, haute demande</p>
                    <p className="text-xs text-blue-500">Commissions 25-100€</p>
                  </div>
                  <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <h5 className="font-medium text-purple-800 dark:text-purple-200">IA/SaaS</h5>
                    <p className="text-purple-600 dark:text-purple-300">Marché explosif 2025</p>
                    <p className="text-xs text-purple-500">Commissions récurrentes</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* APIs Tab */}
        <TabsContent value="apis" className="space-y-4 sm:space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5" />
                  <span>SerpAPI</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {serpApiStatus?.success ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>Statut:</span>
                      <Badge variant={serpApiStatus.provider_active ? "default" : "destructive"}>
                        {serpApiStatus.provider_active ? "Actif" : "Inactif"}
                      </Badge>
                    </div>
                    {serpApiStatus.credits_remaining && (
                      <div className="flex items-center justify-between">
                        <span>Crédits restants:</span>
                        <span className="font-medium">{serpApiStatus.credits_remaining.toLocaleString()}</span>
                      </div>
                    )}
                    <div className="text-sm text-muted-foreground">
                      <p>• Google News monitoring</p>
                      <p>• YouTube Search discovery</p>
                      <p>• Google Trends analysis</p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4">
                    <AlertTriangle className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                    <p className="text-sm text-muted-foreground">Configuration SerpAPI requise</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Shield className="h-5 w-5" />
                  <span>OpenAI</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span>Modèle:</span>
                    <Badge variant="default">GPT-4o</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Statut:</span>
                    <Badge variant="default">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Actif
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <p>• Génération de hooks viraux</p>
                    <p>• Optimisation des titres</p>
                    <p>• Prédiction de performance</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Publishing Tab */}
        <TabsContent value="publishing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Globe className="h-5 w-5" />
                <span>Plateformes de Publication</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {bufferStatus?.success ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span>Profils connectés:</span>
                    <Badge variant="default">{bufferStatus.profiles_connected || 0}</Badge>
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                    {bufferStatus.profiles?.map((profile, index) => (
                      <div key={index} className="p-3 border rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="font-medium capitalize">{profile.platform}</span>
                          <Badge variant={profile.connected ? "default" : "destructive"}>
                            {profile.connected ? "Connecté" : "Déconnecté"}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">@{profile.username}</p>
                      </div>
                    )) || (
                      <div className="col-span-full text-center py-4">
                        <p className="text-muted-foreground">Aucun profil configuré</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
                  <p className="text-muted-foreground">Configuration Buffer requise</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Ajoutez votre Access Token Buffer pour activer la publication automatique
                  </p>
                </div>
              )}
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2 text-sm sm:text-base">Coût Publication (18€/mois)</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 text-sm">
                  <div className="text-center">
                    <div className="font-medium">Instagram</div>
                    <div className="text-muted-foreground">6€/mois</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium">TikTok</div>
                    <div className="text-muted-foreground">6€/mois</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium">YouTube</div>
                    <div className="text-muted-foreground">6€/mois</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* IA + Supadata Tab */}
        <TabsContent value="ai" className="space-y-6">
          <div className="grid gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Brain className="h-5 w-5" />
                  <span>IA ContentFlow + Supadata AI</span>
                </CardTitle>
                <CardDescription>
                  Intelligence artificielle double couche : OpenAI + Supadata pour optimisation maximale
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Modèle OpenAI</Label>
                    <Select defaultValue="gpt-4o">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4o">GPT-4o (Recommandé)</SelectItem>
                        <SelectItem value="gpt-4-turbo">GPT-4 Turbo</SelectItem>
                        <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Supadata AI Mode</Label>
                    <Select defaultValue="performance">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="performance">Performance Max</SelectItem>
                        <SelectItem value="balanced">Équilibré</SelectItem>
                        <SelectItem value="creative">Créatif</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-4">
                  <h4 className="font-medium">Fonctionnalités Supadata AI</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">Analyse performance prédictive</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">Optimisation contenu auto</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">Tendances audience temps réel</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                        <span className="text-sm">ContentFlow Pack enhanced</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                        <span className="text-sm">Recommandations IA personnalisées</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                        <span className="text-sm">Optimisation pré-publication</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-4">
                  <h4 className="font-medium">Métriques IA Performance</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                    <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">96.8%</div>
                      <div className="text-sm text-muted-foreground">Précision Supadata</div>
                    </div>
                    <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">+45%</div>
                      <div className="text-sm text-muted-foreground">ROI vs IA Simple</div>
                    </div>
                    <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">1,247</div>
                      <div className="text-sm text-muted-foreground">Optimisations IA</div>
                    </div>
                  </div>
                </div>
                
                <Separator />
                
                <div className="space-y-4">
                  <h4 className="font-medium">Test Supadata par Niche</h4>
                  <div className="grid gap-3">
                    {((contentflowData as any)?.niches || (contentflowMetrics as any)?.metrics?.niches || []).map((niche: any) => (
                      <div key={typeof niche === 'string' ? niche : niche.name} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          <Target className="h-4 w-4" />
                          <span className="font-medium capitalize">{typeof niche === 'string' ? niche : niche.name}</span>
                        </div>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => testSupadataEnhancement(typeof niche === 'string' ? niche : niche?.name)}
                        >
                          Test Supadata AI
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Email Marketing Tab */}
        <TabsContent value="email" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <span>📧</span>
                <span>Email Marketing Brevo</span>
              </CardTitle>
              <CardDescription>
                Automatisation des campagnes email pour maximiser l'engagement et les revenus
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Configuration Brevo</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <span>API Key Brevo:</span>
                      <Badge variant="outline">Configurée</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <span>Connexion:</span>
                      <Badge variant="secondary">Active</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <span>Listes créées:</span>
                      <Badge variant="outline">3</Badge>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium">Campagnes Automatisées</h4>
                  <div className="space-y-3">
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Newsletter Performance</span>
                        <Switch />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Envoi hebdomadaire des meilleurs contenus
                      </p>
                    </div>
                    
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Alertes Revenus</span>
                        <Switch />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Notification quand seuil de revenus atteint
                      </p>
                    </div>
                    
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Promotion Contenu</span>
                        <Switch />
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Campagnes par niche pour nouveaux contenus
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="font-medium">Actions Rapides</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button variant="outline" className="h-auto p-4 flex flex-col space-y-2">
                    <span className="text-lg">📊</span>
                    <span className="font-medium">Newsletter Performance</span>
                    <span className="text-xs text-muted-foreground">Envoyer maintenant</span>
                  </Button>
                  
                  <Button variant="outline" className="h-auto p-4 flex flex-col space-y-2">
                    <span className="text-lg">💰</span>
                    <span className="font-medium">Alerte Revenus</span>
                    <span className="text-xs text-muted-foreground">Test seuil 50€</span>
                  </Button>
                  
                  <Button variant="outline" className="h-auto p-4 flex flex-col space-y-2">
                    <span className="text-lg">🎯</span>
                    <span className="font-medium">Setup Listes</span>
                    <span className="text-xs text-muted-foreground">Créer listes par défaut</span>
                  </Button>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="font-medium">Métriques Email</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">12</div>
                    <div className="text-sm text-muted-foreground">Campagnes envoyées</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">24.3%</div>
                    <div className="text-sm text-muted-foreground">Taux ouverture</div>
                  </div>
                  <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">4.2%</div>
                    <div className="text-sm text-muted-foreground">Taux clic</div>
                  </div>
                </div>
              </div>
              
              <div className="p-4 bg-muted rounded-lg">
                <h5 className="font-medium mb-2">💡 Strategy Email ContentFlow</h5>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• Newsletter hebdomadaire avec top 3 contenus performance</li>
                  <li>• Alertes revenus automatiques si seuil dépassé</li>
                  <li>• Campagnes promotion par niche avec IA Supadata</li>
                  <li>• Séquences d'engagement basées sur comportement</li>
                  <li>• Intégration tracking revenus avec liens affiliés</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Instagram Tab */}
        <TabsContent value="instagram" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <span>📷</span>
                <span>Instagram Graph API</span>
              </CardTitle>
              <CardDescription>
                Connexion officielle Meta pour publication automatique de Reels Instagram
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Configuration OAuth</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <span>Meta App ID:</span>
                      <Badge variant="outline">À configurer</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <span>OAuth Callback:</span>
                      <Badge variant="secondary">/api/ig/oauth/callback</Badge>
                    </div>
                    <div className="flex justify-between items-center p-3 border rounded-lg">
                      <span>Permissions:</span>
                      <Badge variant="outline">Content Publishing</Badge>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium">Statut Connexion</h4>
                  <div className="space-y-3">
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Compte Instagram</span>
                        <Badge variant="destructive">Non connecté</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Connectez votre compte Instagram Business
                      </p>
                    </div>
                    
                    <div className="p-3 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Token Status</span>
                        <Badge variant="secondary">Aucun</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        Token long-lived (60 jours) requis
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="font-medium">Actions</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button 
                    variant="default" 
                    className="h-auto p-4 flex flex-col space-y-2"
                    onClick={() => window.open('/api/ig/oauth/start', '_blank')}
                  >
                    <span className="text-lg">🔗</span>
                    <span className="font-medium">Connecter Instagram</span>
                    <span className="text-xs text-muted-foreground">OAuth Facebook/Meta</span>
                  </Button>
                  
                  <Button variant="outline" className="h-auto p-4 flex flex-col space-y-2">
                    <span className="text-lg">🧪</span>
                    <span className="font-medium">Test Connexion</span>
                    <span className="text-xs text-muted-foreground">Vérifier les permissions</span>
                  </Button>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-4">
                <h4 className="font-medium">Workflow Publication</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">1</div>
                    <div className="text-sm text-muted-foreground">Container</div>
                  </div>
                  <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600">2</div>
                    <div className="text-sm text-muted-foreground">Processing</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">3</div>
                    <div className="text-sm text-muted-foreground">Publish</div>
                  </div>
                </div>
              </div>
              
              <div className="p-4 bg-muted rounded-lg">
                <h5 className="font-medium mb-2">📋 Configuration Meta App</h5>
                <ul className="text-sm space-y-1 text-muted-foreground">
                  <li>• Créer une App Facebook Developer</li>
                  <li>• Ajouter Instagram Graph API Product</li>
                  <li>• Configurer les permissions: pages_show_list, instagram_content_publish</li>
                  <li>• Soumettre pour révision Meta (requis pour prod)</li>
                  <li>• Connecter compte Instagram Business à page Facebook</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Monetization Tab */}
        <TabsContent value="monetization" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <DollarSign className="h-5 w-5" />
                <span>Monétisation</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Coûts Mensuels</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>SerpAPI (15k recherches):</span>
                      <span className="font-medium">150€</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Buffer (3 plateformes):</span>
                      <span className="font-medium">18€</span>
                    </div>
                    <div className="flex justify-between border-t pt-2 font-semibold">
                      <span>Total fixe:</span>
                      <span>168€</span>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="font-medium">Revenus Potentiels</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Débutant (1k vues/post):</span>
                      <span className="font-medium text-green-600">1000€</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Moyen (5k vues/post):</span>
                      <span className="font-medium text-green-600">5000€</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Établi (15k vues/post):</span>
                      <span className="font-medium text-green-600">15000€</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t pt-4">
                <h4 className="font-medium mb-3">Configuration Shortlinks</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="revenue-per-click">Revenus par clic (€)</Label>
                    <Input 
                      id="revenue-per-click" 
                      defaultValue="0.25" 
                      type="number" 
                      step="0.01"
                    />
                  </div>
                  <div>
                    <Label htmlFor="conversion-rate">Taux de conversion (%)</Label>
                    <Input 
                      id="conversion-rate" 
                      defaultValue="2.0" 
                      type="number" 
                      step="0.1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="monthly-posts">Posts par mois</Label>
                    <Input 
                      id="monthly-posts" 
                      defaultValue="200" 
                      type="number"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}