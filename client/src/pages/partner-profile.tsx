import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { 
  User, 
  Euro, 
  Settings, 
  CreditCard, 
  DollarSign,
  TrendingUp,
  Calendar,
  LogOut,
  Save,
  Eye,
  EyeOff,
  BarChart3,
  Activity,
  Clock,
  Users,
  FileText,
  Zap,
  Target,
  MousePointer,
  Share2,
  Smartphone,
  Laptop,
  Globe,
  AlertCircle,
  CheckCircle,
  ArrowUp,
  ArrowDown,
  Minus
} from "lucide-react";

interface PartnerProfile {
  id: string;
  email: string;
  name: string;
  created_at: string;
  revenue_share_pct: number;
  total_earnings_eur: number;
  pending_payout_eur: number;
  last_payout_date?: string;
}

interface PaymentMethod {
  id: string;
  type: 'paypal' | 'stripe';
  email?: string;
  stripe_account_id?: string;
  is_verified: boolean;
  created_at: string;
}

interface EarningsStats {
  last_30_days_eur: number;
  last_7_days_eur: number;
  last_24_hours_eur: number;
  total_clicks: number;
  avg_epc_eur: number;
  conversion_rate: number;
  total_posts: number;
  active_campaigns: number;
}

interface PartnerStatistics {
  performance: {
    total_impressions: number;
    total_clicks: number;
    total_conversions: number;
    click_through_rate: number;
    conversion_rate: number;
    avg_session_duration: number;
  };
  content: {
    total_posts_created: number;
    total_posts_published: number;
    posts_pending_approval: number;
    avg_engagement_rate: number;
    top_performing_platform: string;
    content_categories: string[];
  };
  revenue: {
    total_revenue_eur: number;
    best_performing_day: number;
    revenue_by_platform: {
      instagram: number;
      tiktok: number;
      youtube: number;
      twitter: number;
      linkedin: number;
    };
    monthly_trend: number[];
    weekly_trend: number[];
  };
  activity: {
    last_login: string;
    account_age_days: number;
    total_sessions: number;
    posts_this_week: number;
    posts_this_month: number;
  };
}

interface ContentAnalytics {
  recent_posts: any[];
  top_performing_posts: any[];
  content_performance_by_type: {
    video: { posts: number; avg_engagement: number; total_revenue: number };
    image: { posts: number; avg_engagement: number; total_revenue: number };
    text: { posts: number; avg_engagement: number; total_revenue: number };
  };
  posting_frequency: {
    daily_average: number;
    weekly_total: number;
    monthly_total: number;
  };
  audience_insights: {
    total_reach: number;
    unique_visitors: number;
    returning_visitors: number;
    demographics: {
      age_groups: Record<string, number>;
      locations: Record<string, number>;
      interests: string[];
    };
  };
}

export default function PartnerProfilePage() {
  const [activeTab, setActiveTab] = useState("profile");
  const [showApiKey, setShowApiKey] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Queries
  const { data: profile, isLoading: profileLoading } = useQuery<PartnerProfile>({
    queryKey: ["/api/partner/profile"]
  });

  const { data: paymentMethods } = useQuery<PaymentMethod[]>({
    queryKey: ["/api/partner/payment-methods"]
  });

  const { data: earnings } = useQuery<EarningsStats>({
    queryKey: ["/api/partner/earnings"]
  });

  const { data: statistics } = useQuery<PartnerStatistics>({
    queryKey: ["/api/partner/statistics"]
  });

  const { data: contentAnalytics } = useQuery<ContentAnalytics>({
    queryKey: ["/api/partner/content-analytics"]
  });

  // Mutations
  const updateProfileMutation = useMutation({
    mutationFn: async (data: { name?: string; email?: string }) => {
      const response = await fetch("/api/partner/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(data)
      });
      if (!response.ok) {
        const errorData = await response.text();
        console.error("Profile update error:", response.status, errorData);
        throw new Error(`Erreur ${response.status}: ${errorData}`);
      }
      return response.json();
    },
    onSuccess: (data) => {
      toast({ 
        title: "Profil mis à jour !", 
        description: `Informations sauvegardées avec succès !` 
      });
      // Force refresh of profile data
      queryClient.invalidateQueries({ queryKey: ["/api/partner/profile"] });
      queryClient.refetchQueries({ queryKey: ["/api/partner/profile"] });
    },
    onError: (error: any) => {
      toast({ 
        title: "Erreur", 
        description: error.message || "Impossible de mettre à jour le profil",
        variant: "destructive"
      });
    }
  });

  const addPaypalMutation = useMutation({
    mutationFn: async (email: string) => {
      const response = await fetch("/api/partner/payment-methods", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "paypal", email })
      });
      return response.json();
    },
    onSuccess: () => {
      toast({ title: "PayPal ajouté !" });
      queryClient.invalidateQueries({ queryKey: ["/api/partner/payment-methods"] });
    }
  });

  const requestPayoutMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch("/api/partner/request-payout", {
        method: "POST"
      });
      return response.json();
    },
    onSuccess: (data) => {
      if (data.success) {
        toast({ 
          title: "Demande de paiement envoyée !",
          description: `Paiement de €${data.amount} en cours de traitement.`
        });
        queryClient.invalidateQueries({ queryKey: ["/api/partner/profile"] });
      }
    }
  });

  const handleLogout = () => {
    // Clear partner session
    document.cookie = "partner_id=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = "/partner-auth";
  };

  const handleUpdateProfile = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const name = formData.get('name') as string;
    const email = formData.get('email') as string;
    
    const updateData: { name?: string; email?: string } = {};
    if (name.trim()) updateData.name = name.trim();
    if (email.trim() && email.includes('@')) updateData.email = email.trim();
    
    updateProfileMutation.mutate(updateData);
  };

  const handleAddPaypal = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const email = formData.get('paypal_email') as string;
    addPaypalMutation.mutate(email);
  };

  if (profileLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Card>
          <CardContent className="pt-6">
            <p>Erreur de chargement du profil</p>
            <Button onClick={handleLogout} className="mt-4">Retour</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-4 md:p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between space-y-4 md:space-y-0">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
              Espace Partenaire
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Bienvenue, {profile.name || profile.email}
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <Badge variant="outline" className="bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300">
              Revenue Share: {profile.revenue_share_pct}%
            </Badge>
            <Button 
              variant="outline" 
              onClick={handleLogout}
              data-testid="button-logout"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </div>

        {/* Earnings Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-green-100">Gains totaux</p>
                  <p className="text-2xl font-bold">
                    €{profile.total_earnings_eur.toFixed(2)}
                  </p>
                  <p className="text-xs text-green-100 mt-1">
                    {profile.total_earnings_eur === 0 ? "Commencez à gagner !" : "Total cumulé"}
                  </p>
                </div>
                <Euro className="w-10 h-10 text-green-100" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-100">En attente</p>
                  <p className="text-2xl font-bold">
                    €{profile.pending_payout_eur.toFixed(2)}
                  </p>
                  <p className="text-xs text-blue-100 mt-1">
                    {profile.pending_payout_eur < 10 ? "Min €10 pour paiement" : "Prêt pour paiement"}
                  </p>
                </div>
                <DollarSign className="w-10 h-10 text-blue-100" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-100">30 derniers jours</p>
                  <p className="text-2xl font-bold">
                    €{earnings?.last_30_days_eur?.toFixed(2) || '0.00'}
                  </p>
                  <p className="text-xs text-purple-100 mt-1">
                    {earnings?.last_7_days_eur ? `+€${earnings.last_7_days_eur.toFixed(2)} cette semaine` : "Pas encore de revenus"}
                  </p>
                </div>
                <TrendingUp className="w-10 h-10 text-purple-100" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-orange-100">EPC moyen</p>
                  <p className="text-2xl font-bold">
                    €{earnings?.avg_epc_eur?.toFixed(3) || '0.000'}
                  </p>
                  <p className="text-xs text-orange-100 mt-1">
                    {earnings?.total_clicks || 0} clics au total
                  </p>
                </div>
                <MousePointer className="w-10 h-10 text-orange-100" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Performance Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Performance générale</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Taux de clic</span>
                  <span className="text-sm font-bold">
                    {statistics?.performance.click_through_rate?.toFixed(2) || '0.00'}%
                  </span>
                </div>
                <Progress value={statistics?.performance.click_through_rate || 0} className="h-2" />
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Conversion</span>
                  <span className="text-sm font-bold">
                    {statistics?.performance.conversion_rate?.toFixed(2) || '0.00'}%
                  </span>
                </div>
                <Progress value={statistics?.performance.conversion_rate || 0} className="h-2" />

                <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                  {statistics?.performance.total_impressions || 0} impressions • {statistics?.performance.total_conversions || 0} conversions
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Contenu créé</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {statistics?.content.total_posts_created || 0}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {statistics?.content.total_posts_published || 0} publiés • {statistics?.content.posts_pending_approval || 0} en attente
                </div>
                
                <div className="flex items-center space-x-2 mt-3">
                  <Badge variant={statistics?.content.total_posts_published ? "default" : "secondary"}>
                    {statistics?.content.top_performing_platform || "Aucune plateforme active"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Activité récente</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Cette semaine</span>
                  <span className="text-sm font-bold">{statistics?.activity.posts_this_week || 0} posts</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">Ce mois</span>
                  <span className="text-sm font-bold">{statistics?.activity.posts_this_month || 0} posts</span>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {statistics?.activity.total_sessions || 0} sessions • Compte créé il y a {statistics?.activity.account_age_days || 0} jours
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Revenue by Platform */}
        {statistics?.revenue && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Share2 className="w-5 h-5 mr-2" />
                Revenus par plateforme
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {Object.entries(statistics.revenue.revenue_by_platform).map(([platform, revenue]) => (
                  <div key={platform} className="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div className="text-sm font-medium capitalize mb-1">{platform}</div>
                    <div className="text-lg font-bold text-green-600">€{revenue.toFixed(2)}</div>
                    <div className="text-xs text-gray-500">
                      {revenue === 0 ? "Pas encore actif" : "Total généré"}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Getting Started Guide for Zero State */}
        {profile.total_earnings_eur === 0 && (
          <Card className="border-blue-200 bg-blue-50 dark:bg-blue-900 dark:border-blue-800">
            <CardHeader>
              <CardTitle className="flex items-center text-blue-800 dark:text-blue-200">
                <Zap className="w-5 h-5 mr-2" />
                Premiers pas pour commencer à gagner
              </CardTitle>
            </CardHeader>
            <CardContent className="text-blue-700 dark:text-blue-300">
              <div className="grid md:grid-cols-3 gap-4">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">1</div>
                  <div>
                    <div className="font-medium">Connectez vos comptes</div>
                    <div className="text-sm opacity-80">Connectez Instagram, TikTok, ou YouTube</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">2</div>
                  <div>
                    <div className="font-medium">Créez du contenu</div>
                    <div className="text-sm opacity-80">Utilisez BYOP pour publier facilement</div>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">3</div>
                  <div>
                    <div className="font-medium">Gagnez des revenus</div>
                    <div className="text-sm opacity-80">40% de commission sur tous les clics</div>
                  </div>
                </div>
              </div>
              <div className="mt-4 p-3 bg-blue-100 dark:bg-blue-800 rounded-lg">
                <div className="text-sm">
                  <strong>💡 Astuce :</strong> Plus vous publiez régulièrement, plus vos revenus augmentent ! Commencez par 1-2 posts par jour.
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="profile">
              <User className="w-4 h-4 mr-2" />
              Profil
            </TabsTrigger>
            <TabsTrigger value="analytics">
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="payments">
              <CreditCard className="w-4 h-4 mr-2" />
              Paiements
            </TabsTrigger>
            <TabsTrigger value="api">
              <Settings className="w-4 h-4 mr-2" />
              API
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Informations du profil</CardTitle>
                <CardDescription>
                  Gérez vos informations personnelles
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleUpdateProfile} className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      defaultValue={profile.email || ''}
                      placeholder="votre@email.com"
                      data-testid="input-partner-email"
                      type="email"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="name">Nom d'affichage</Label>
                    <Input
                      id="name"
                      name="name"
                      defaultValue={profile.name || ''}
                      placeholder="Votre nom ou nom de marque"
                      data-testid="input-partner-name"
                    />
                  </div>
                  
                  <Button 
                    type="submit" 
                    disabled={updateProfileMutation.isPending}
                    data-testid="button-save-profile"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {updateProfileMutation.isPending ? "Sauvegarde..." : "Sauvegarder"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics">
            <div className="space-y-6">
              {/* Content Performance */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <FileText className="w-5 h-5 mr-2" />
                    Performance du contenu
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {contentAnalytics?.content_performance_by_type ? (
                    <div className="grid md:grid-cols-3 gap-4">
                      {Object.entries(contentAnalytics.content_performance_by_type).map(([type, data]) => (
                        <div key={type} className="p-4 border rounded-lg">
                          <div className="text-sm font-medium capitalize mb-2">{type}</div>
                          <div className="space-y-1">
                            <div className="flex justify-between text-sm">
                              <span>Posts:</span>
                              <span className="font-bold">{data.posts}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span>Engagement:</span>
                              <span className="font-bold">{data.avg_engagement.toFixed(2)}%</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span>Revenus:</span>
                              <span className="font-bold text-green-600">€{data.total_revenue.toFixed(2)}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>Aucun contenu créé pour le moment</p>
                      <p className="text-sm">Commencez à publier pour voir vos analytics !</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Audience Insights */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Users className="w-5 h-5 mr-2" />
                    Audience & Portée
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {contentAnalytics?.audience_insights && contentAnalytics.audience_insights.total_reach > 0 ? (
                    <div className="grid md:grid-cols-3 gap-6">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-600">{contentAnalytics.audience_insights.total_reach.toLocaleString()}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Portée totale</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">{contentAnalytics.audience_insights.unique_visitors.toLocaleString()}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Visiteurs uniques</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-purple-600">{contentAnalytics.audience_insights.returning_visitors.toLocaleString()}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">Visiteurs récurrents</div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>Aucune donnée d'audience disponible</p>
                      <p className="text-sm">Publiez du contenu pour commencer à toucher votre audience</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Posting Frequency */}
              <div className="grid md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Calendar className="w-5 h-5 mr-2" />
                      Fréquence de publication
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Moyenne quotidienne</span>
                        <span className="font-bold">{contentAnalytics?.posting_frequency.daily_average || 0}</span>
                      </div>
                      <Progress value={(contentAnalytics?.posting_frequency.daily_average || 0) * 20} className="h-2" />
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Cette semaine</span>
                        <span className="font-bold">{contentAnalytics?.posting_frequency.weekly_total || 0}</span>
                      </div>
                      <Progress value={(contentAnalytics?.posting_frequency.weekly_total || 0) * 5} className="h-2" />
                      
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Ce mois</span>
                        <span className="font-bold">{contentAnalytics?.posting_frequency.monthly_total || 0}</span>
                      </div>
                      <Progress value={(contentAnalytics?.posting_frequency.monthly_total || 0) * 2} className="h-2" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Target className="w-5 h-5 mr-2" />
                      Objectifs de performance
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm">Posts quotidiens</span>
                          <span className="text-sm">{contentAnalytics?.posting_frequency.daily_average || 0}/2</span>
                        </div>
                        <Progress value={((contentAnalytics?.posting_frequency.daily_average || 0) / 2) * 100} className="h-2" />
                      </div>
                      
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm">Taux d'engagement</span>
                          <span className="text-sm">{statistics?.content.avg_engagement_rate?.toFixed(1) || 0}%/5%</span>
                        </div>
                        <Progress value={((statistics?.content.avg_engagement_rate || 0) / 5) * 100} className="h-2" />
                      </div>
                      
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm">Revenus mensuels</span>
                          <span className="text-sm">€{earnings?.last_30_days_eur?.toFixed(2) || '0.00'}/€100</span>
                        </div>
                        <Progress value={((earnings?.last_30_days_eur || 0) / 100) * 100} className="h-2" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Recent Activity */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Activity className="w-5 h-5 mr-2" />
                    Activité récente
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {contentAnalytics?.recent_posts && contentAnalytics.recent_posts.length > 0 ? (
                    <div className="space-y-3">
                      {contentAnalytics.recent_posts.map((post: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <div className="font-medium">{post.title || `Post ${index + 1}`}</div>
                            <div className="text-sm text-gray-600 dark:text-gray-400">{post.platform} • {post.date}</div>
                          </div>
                          <Badge variant={post.status === 'published' ? 'default' : 'secondary'}>
                            {post.status || 'publié'}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <p>Aucune activité récente</p>
                      <p className="text-sm">Votre activité de publication apparaîtra ici</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="payments">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Méthodes de paiement</CardTitle>
                  <CardDescription>
                    Configurez vos comptes PayPal et Stripe pour recevoir vos gains
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {paymentMethods?.map((method) => (
                    <div key={method.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <CreditCard className="w-5 h-5" />
                        <div>
                          <p className="font-medium capitalize">{method.type}</p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {method.email || method.stripe_account_id}
                          </p>
                        </div>
                      </div>
                      <Badge variant={method.is_verified ? "default" : "secondary"}>
                        {method.is_verified ? "Vérifié" : "En attente"}
                      </Badge>
                    </div>
                  ))}

                  <form onSubmit={handleAddPaypal} className="border-t pt-4">
                    <h4 className="font-medium mb-3">Ajouter PayPal</h4>
                    <div className="flex space-x-2">
                      <Input
                        name="paypal_email"
                        type="email"
                        placeholder="votre@paypal.com"
                        required
                        data-testid="input-paypal-email"
                      />
                      <Button 
                        type="submit" 
                        disabled={addPaypalMutation.isPending}
                        data-testid="button-add-paypal"
                      >
                        {addPaypalMutation.isPending ? "Ajout..." : "Ajouter"}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Demande de paiement</CardTitle>
                  <CardDescription>
                    Minimum €10 - Paiements traités sous 48h
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div>
                      <p className="font-medium">Montant disponible</p>
                      <p className="text-2xl font-bold text-green-600">
                        €{profile.pending_payout_eur.toFixed(2)}
                      </p>
                    </div>
                    <Button
                      onClick={() => requestPayoutMutation.mutate()}
                      disabled={profile.pending_payout_eur < 10 || requestPayoutMutation.isPending || !paymentMethods?.some(m => m.is_verified)}
                      data-testid="button-request-payout"
                    >
                      {requestPayoutMutation.isPending ? "Demande..." : "Demander le paiement"}
                    </Button>
                  </div>
                  
                  {profile.last_payout_date && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                      Dernier paiement: {new Date(profile.last_payout_date).toLocaleDateString('fr-FR')}
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="api">
            <Card>
              <CardHeader>
                <CardTitle>Accès API</CardTitle>
                <CardDescription>
                  Utilisez votre ID partenaire pour accéder aux APIs BYOP
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>ID Partenaire</Label>
                  <div className="flex space-x-2">
                    <Input
                      value={showApiKey ? profile.id : "••••••••••••••••"}
                      readOnly
                      className="bg-gray-100 dark:bg-gray-700"
                    />
                    <Button
                      variant="outline"
                      onClick={() => setShowApiKey(!showApiKey)}
                      data-testid="button-toggle-api-key"
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>
                
                <div className="p-4 bg-blue-50 dark:bg-blue-900 rounded-lg">
                  <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2">
                    Comment utiliser l'API
                  </h4>
                  <code className="text-xs text-blue-800 dark:text-blue-200 block">
                    curl -H "X-Partner-ID: {profile.id}" https://api.contentflow.com/api/byop/submit
                  </code>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}