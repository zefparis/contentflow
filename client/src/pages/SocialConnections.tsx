import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { Plus, ExternalLink, Settings, CheckCircle, AlertCircle } from "lucide-react";

interface SocialConnection {
  id: string;
  partnerId: string;
  platform: string;
  platformUserId: string;
  accountName: string;
  accountUrl: string;
  isActive: boolean | string;
  permissions: string[];
  createdAt: string;
}

const AVAILABLE_PLATFORMS = [
  { 
    id: 'instagram', 
    name: 'Instagram', 
    description: 'Publiez des photos et stories sur Instagram',
    color: 'bg-pink-500',
    instructions: 'Connectez votre compte Instagram Business pour publier automatiquement'
  },
  { 
    id: 'facebook', 
    name: 'Facebook', 
    description: 'Partagez sur votre page Facebook',
    color: 'bg-blue-600',
    instructions: 'Connectez votre page Facebook pour publier automatiquement'
  },
  { 
    id: 'twitter', 
    name: 'Twitter/X', 
    description: 'Tweetez votre contenu',
    color: 'bg-black',
    instructions: 'Connectez votre compte Twitter pour tweeter automatiquement'
  },
  { 
    id: 'tiktok', 
    name: 'TikTok', 
    description: 'Publiez des vidéos sur TikTok',
    color: 'bg-black',
    instructions: 'Connectez votre compte TikTok pour publier automatiquement'
  },
  { 
    id: 'linkedin', 
    name: 'LinkedIn', 
    description: 'Partagez sur votre profil LinkedIn',
    color: 'bg-blue-700',
    instructions: 'Connectez votre profil LinkedIn pour publier automatiquement'
  },
  { 
    id: 'youtube', 
    name: 'YouTube', 
    description: 'Publiez des YouTube Shorts',
    color: 'bg-red-600',
    instructions: 'Connectez votre chaîne YouTube pour publier des Shorts'
  }
];

export default function SocialConnections() {
  const [showConnectForm, setShowConnectForm] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [formData, setFormData] = useState({
    platformUserId: '',
    accountName: '',
    accountUrl: '',
    accessToken: '',
  });
  
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch social connections
  const { data: socialData, isLoading } = useQuery({
    queryKey: ['/api/social/connections'],
    staleTime: 30000,
  });

  // Connect social media mutation
  const connectMutation = useMutation({
    mutationFn: async (connectionData: any) => {
      return await apiRequest("POST", "/api/social/connect", connectionData);
    },
    onSuccess: () => {
      toast({
        title: "Connexion réussie",
        description: "Votre compte a été connecté avec succès !",
      });
      queryClient.invalidateQueries({ queryKey: ['/api/social/connections'] });
      setShowConnectForm(false);
      setFormData({ platformUserId: '', accountName: '', accountUrl: '', accessToken: '' });
      setSelectedPlatform('');
    },
    onError: (error: any) => {
      toast({
        title: "Erreur de connexion",
        description: error.message || "Impossible de connecter le compte",
        variant: "destructive",
      });
    },
  });

  const connections: SocialConnection[] = (socialData as any)?.data || [];
  const connectedPlatforms = connections.map(c => c.platform);

  const handleConnect = () => {
    if (!selectedPlatform || !formData.platformUserId) return;

    const platform = AVAILABLE_PLATFORMS.find(p => p.id === selectedPlatform);
    if (!platform) return;

    connectMutation.mutate({
      platform: selectedPlatform,
      platformUserId: formData.platformUserId,
      accountName: formData.accountName || null,
      accountUrl: formData.accountUrl || null,
      accessToken: formData.accessToken || null,
      permissions: ['publish_content', 'read_insights']
    });
  };

  const handleOAuthConnect = (platformId: string) => {
    // Configuration OAuth pour chaque plateforme
    const oauthConfigs = {
      instagram: {
        name: 'Instagram',
        description: 'Connectez votre compte Instagram Business pour publier automatiquement des posts et stories.',
        requirements: [
          'Compte Instagram Business ou Creator',
          'Page Facebook liée au compte Instagram',
          'App Facebook Developer configurée'
        ]
      },
      facebook: {
        name: 'Facebook',
        description: 'Connectez votre page Facebook pour publier automatiquement des posts.',
        requirements: [
          'Page Facebook (pas de profil personnel)',
          'Droits admin sur la page',
          'App Facebook Developer configurée'
        ]
      },
      youtube: {
        name: 'YouTube',
        description: 'Connectez votre chaîne YouTube pour publier des Shorts automatiquement.',
        requirements: [
          'Chaîne YouTube active',
          'Projet Google Cloud configuré',
          'YouTube Data API v3 activée'
        ]
      },
      tiktok: {
        name: 'TikTok',
        description: 'Connectez votre compte TikTok for Business pour publier automatiquement.',
        requirements: [
          'Compte TikTok for Business',
          'App TikTok Developer configurée',
          'Validation du domaine'
        ]
      }
    };

    const config = oauthConfigs[platformId as keyof typeof oauthConfigs];
    
    if (!config) {
      toast({
        title: "Plateforme non supportée",
        description: `La connexion OAuth pour ${platformId} n'est pas encore disponible.`,
        variant: "destructive"
      });
      return;
    }

    const message = `🔗 Connexion OAuth ${config.name}\n\n` +
      `${config.description}\n\n` +
      `Pré-requis nécessaires :\n` +
      config.requirements.map(req => `• ${req}`).join('\n') + '\n\n' +
      `Cette fonctionnalité nécessite une configuration technique avancée.\n` +
      `Voulez-vous commencer par une connexion manuelle (email seulement) ?`;

    const useManual = window.confirm(message);

    if (useManual) {
      setSelectedPlatform(platformId);
      setShowConnectForm(true);
    } else {
      toast({
        title: "Configuration OAuth",
        description: `Pour configurer l'OAuth ${config.name}, contactez le support technique ou consultez la documentation.`,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">Réseaux Sociaux</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Connectez vos comptes pour publier automatiquement votre contenu
          </p>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Comptes Connectés
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                {connections.filter(c => c.isActive === 'true').length}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {connections.length === 0 ? 'Aucun compte connecté' : 'Prêts pour la publication'}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                <AlertCircle className="h-5 w-5 text-blue-500" />
                Plateformes Disponibles
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {AVAILABLE_PLATFORMS.length - connectedPlatforms.length}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Plateformes à connecter
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Connected Accounts */}
        {connections.length > 0 && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Comptes Connectés</h2>
            <div className="grid gap-4 md:grid-cols-2">
              {connections.map((connection) => {
                const platform = AVAILABLE_PLATFORMS.find(p => p.id === connection.platform);
                const isActive = connection.isActive === true || connection.isActive === 'true';
                return (
                  <Card key={connection.id} className={`overflow-hidden border-2 ${isActive ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-950/20' : 'border-yellow-200 dark:border-yellow-800 bg-yellow-50/50 dark:bg-yellow-950/20'} hover:shadow-md transition-all`}>
                    <CardContent className="p-5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-full ${platform?.color || 'bg-gray-500'} flex items-center justify-center shadow-lg`}>
                            <span className="text-white font-bold text-lg">
                              {platform?.name?.charAt(0) || connection.platform.charAt(0).toUpperCase()}
                            </span>
                          </div>
                          <div>
                            <h3 className="font-semibold text-lg capitalize text-gray-900 dark:text-white">{platform?.name || connection.platform}</h3>
                            <p className="text-base text-gray-700 dark:text-gray-300 font-medium">
                              {connection.accountName || connection.platformUserId}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                              <CheckCircle className={`h-4 w-4 ${isActive ? 'text-green-600 dark:text-green-400' : 'text-yellow-500 dark:text-yellow-400'}`} />
                              <span className={`text-sm font-medium ${isActive ? 'text-green-700 dark:text-green-300' : 'text-yellow-700 dark:text-yellow-300'}`}>
                                {isActive ? 'Prêt à publier' : 'OAuth requis pour publier'}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge 
                            variant={isActive ? 'default' : 'secondary'}
                            className={`font-semibold px-3 py-1 ${isActive ? 'bg-green-600 dark:bg-green-700 text-white hover:bg-green-700 dark:hover:bg-green-800' : 'bg-yellow-600 dark:bg-yellow-700 text-white hover:bg-yellow-700 dark:hover:bg-yellow-800'}`}
                          >
                            {isActive ? '✅ Connecté' : '⚠️ Partiellement connecté'}
                          </Badge>
                          {connection.accountUrl && (
                            <Button variant="outline" size="sm" asChild className="border-2 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800">
                              <a href={connection.accountUrl} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="h-4 w-4" />
                              </a>
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Available Platforms */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Plateformes Disponibles</h2>
            <Button 
              onClick={() => setShowConnectForm(true)}
              className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white dark:from-purple-700 dark:to-pink-700 dark:hover:from-purple-800 dark:hover:to-pink-800"
              data-testid="button-add-connection"
            >
              <Plus className="h-4 w-4" />
              Ajouter un Compte
            </Button>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {AVAILABLE_PLATFORMS.map((platform) => {
              const isConnected = connectedPlatforms.includes(platform.id);
              return (
                <Card key={platform.id} className={`overflow-hidden border-2 hover:shadow-lg transition-all ${isConnected ? 'border-green-300 dark:border-green-700 bg-green-50 dark:bg-green-950/20 ring-2 ring-green-200 dark:ring-green-800' : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-purple-300 dark:hover:border-purple-600'}`}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-full ${platform.color} flex items-center justify-center shadow-md`}>
                        <span className="text-white font-bold text-lg">
                          {platform.name.charAt(0)}
                        </span>
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-lg font-bold text-gray-900 dark:text-white">{platform.name}</CardTitle>
                        {isConnected && (
                          <Badge className="mt-2 bg-green-600 dark:bg-green-700 text-white hover:bg-green-700 dark:hover:bg-green-800 font-semibold">
                            ✅ Connecté
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="mb-4 text-gray-700 dark:text-gray-300 font-medium text-base">
                      {platform.description}
                    </CardDescription>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
                      {platform.instructions}
                    </p>
                    {isConnected ? (
                      <div className="space-y-3">
                        <div className="text-center p-3 bg-green-100 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-800">
                          <p className="text-green-800 dark:text-green-300 font-semibold">
                            📧 Email connecté
                          </p>
                          <p className="text-green-700 dark:text-green-400 text-sm mt-1">
                            Pour publier automatiquement, connectez via OAuth
                          </p>
                        </div>
                        <Button 
                          className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-2"
                          onClick={() => handleOAuthConnect(platform.id)}
                          data-testid={`button-oauth-${platform.id}`}
                        >
                          <Settings className="h-4 w-4 mr-2" />
                          Autoriser la publication
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Button 
                          className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 dark:from-purple-700 dark:to-pink-700 dark:hover:from-purple-800 dark:hover:to-pink-800 text-white font-semibold py-3 shadow-lg"
                          onClick={() => handleOAuthConnect(platform.id)}
                          data-testid={`button-oauth-connect-${platform.id}`}
                        >
                          <Settings className="h-5 w-5 mr-2" />
                          Connexion OAuth
                        </Button>
                        <Button 
                          variant="outline"
                          className="w-full border-2 border-gray-300 dark:border-gray-600 text-sm"
                          onClick={() => {
                            setSelectedPlatform(platform.id);
                            setShowConnectForm(true);
                          }}
                          data-testid={`button-manual-connect-${platform.id}`}
                        >
                          Connexion manuelle (email seulement)
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Connection Form Modal */}
        {showConnectForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-black dark:bg-opacity-70 flex items-center justify-center p-4 z-50">
            <Card className="max-w-sm w-full max-h-[90vh] overflow-y-auto bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg text-gray-900 dark:text-white">
                  Connecter {AVAILABLE_PLATFORMS.find(p => p.id === selectedPlatform)?.name}
                </CardTitle>
                <CardDescription className="text-sm text-gray-600 dark:text-gray-400">
                  Connexion manuelle (email seulement)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                  <h4 className="font-semibold text-blue-900 dark:text-blue-300 mb-1 text-sm">📝 Information requise</h4>
                  <p className="text-blue-800 dark:text-blue-400 text-xs">
                    Pour commencer, nous avons seulement besoin de votre email ou nom d'utilisateur.
                  </p>
                </div>

                <div>
                  <Label htmlFor="platformUserId" className="text-sm font-semibold text-gray-900 dark:text-white">
                    Email ou nom d'utilisateur *
                  </Label>
                  <Input
                    id="platformUserId"
                    value={formData.platformUserId}
                    onChange={(e) => setFormData({...formData, platformUserId: e.target.value})}
                    placeholder="votre@email.com"
                    className="mt-1 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                    data-testid="input-platform-user-id"
                  />
                </div>

                <div>
                  <Label htmlFor="accountName" className="text-sm font-medium text-gray-900 dark:text-white">
                    Nom d'affichage (optionnel)
                  </Label>
                  <Input
                    id="accountName"
                    value={formData.accountName}
                    onChange={(e) => setFormData({...formData, accountName: e.target.value})}
                    placeholder="Nom public"
                    className="mt-1 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                    data-testid="input-account-name"
                  />
                </div>

                <div>
                  <Label htmlFor="accountUrl" className="text-sm font-medium text-gray-900 dark:text-white">
                    URL du profil (optionnel)
                  </Label>
                  <Input
                    id="accountUrl"
                    value={formData.accountUrl}
                    onChange={(e) => setFormData({...formData, accountUrl: e.target.value})}
                    placeholder="https://instagram.com/nom"
                    className="mt-1 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                    data-testid="input-account-url"
                  />
                </div>

                <div className="border-t border-gray-200 dark:border-gray-600 pt-3">
                  <Label htmlFor="accessToken" className="text-sm font-medium text-gray-900 dark:text-white">
                    Token d'API (optionnel)
                  </Label>
                  <Input
                    id="accessToken"
                    type="password"
                    value={formData.accessToken}
                    onChange={(e) => setFormData({...formData, accessToken: e.target.value})}
                    placeholder="Token API"
                    className="mt-1 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
                    data-testid="input-access-token"
                  />
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    <strong>Pas obligatoire !</strong> Pour OAuth plus tard.
                  </p>
                </div>

                <div className="flex gap-2 pt-3">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setShowConnectForm(false);
                      setSelectedPlatform('');
                      setFormData({ platformUserId: '', accountName: '', accountUrl: '', accessToken: '' });
                    }}
                    className="flex-1 h-8 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-600 text-sm"
                  >
                    Annuler
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleConnect}
                    disabled={!formData.platformUserId || connectMutation.isPending}
                    className="flex-1 h-8 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 dark:from-purple-700 dark:to-pink-700 dark:hover:from-purple-800 dark:hover:to-pink-800 text-white text-sm"
                    data-testid="button-connect-submit"
                  >
                    {connectMutation.isPending ? "Connexion..." : "Connecter"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Help Section */}
        <div className="grid md:grid-cols-2 gap-6">
          <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
            <CardContent className="p-6">
              <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-3">💡 Comment ça marche ?</h3>
              <div className="space-y-2 text-blue-800 dark:text-blue-400 text-sm">
                <p>1. <strong>Connectez vos comptes</strong> - Ajoutez vos réseaux sociaux</p>
                <p>2. <strong>Autorisez la publication</strong> - OAuth pour publier automatiquement</p>
                <p>3. <strong>Créez du contenu</strong> - IA génère du contenu engageant</p>
                <p>4. <strong>Gagnez des revenus</strong> - Partage automatique des revenus</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800">
            <CardContent className="p-6">
              <h3 className="font-semibold text-amber-900 dark:text-amber-300 mb-3">🔐 Pourquoi OAuth ?</h3>
              <div className="space-y-2 text-amber-800 dark:text-amber-400 text-sm">
                <p><strong>Connexion Email</strong> : Identification de base (actuel)</p>
                <p><strong>OAuth requis pour</strong> : Publication automatique sécurisée</p>
                <p><strong>Configuration</strong> : Apps développeur sur chaque plateforme</p>
                <p><strong>Sécurité</strong> : Tokens d'accès officiels et révocables</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}