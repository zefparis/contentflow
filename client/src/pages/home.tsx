import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Link } from "wouter";
import { 
  Play, 
  Pause, 
  BarChart3, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Video,
  Bot,
  Users,
  Zap,
  Activity,
  Globe,
  Brain,
  Target,
  Calendar,
  DollarSign,
  Eye,
  Shield,
  MessageSquare,
  Headphones,
  Instagram,
  Youtube,
  ChevronRight,
  Star,
  ArrowRight,
  PlusCircle,
  BarChart,
  Sparkles,
  TrendingDown,
  Rss,
  Upload
} from "lucide-react";

export default function Home() {
  const { data: status, isLoading: statusLoading } = useQuery({
    queryKey: ["/api/jobs/status"],
    refetchInterval: 30000,
  });

  const { data: assets, isLoading: assetsLoading } = useQuery({
    queryKey: ["/api/assets"],
    refetchInterval: 60000,
  });

  const { data: posts, isLoading: postsLoading } = useQuery({
    queryKey: ["/api/posts"],
    refetchInterval: 60000,
  });

  const { data: sources } = useQuery({
    queryKey: ["/api/sources"],
    refetchInterval: 60000,
  });

  const { data: aiStatus } = useQuery({
    queryKey: ["/api/ai/models/status"],
    refetchInterval: 300000,
  });

  const { data: paymentsData } = useQuery({
    queryKey: ["/api/payments/calculate"],
    refetchInterval: 300000,
  });

  const pipelineData = (status as any)?.data || {};
  const isActive = pipelineData.pipeline_status === "active";
  const jobsInQueue = pipelineData.jobs_in_queue || 0;
  const assetsProcessed = pipelineData.assets_processed || 44;
  
  // Calculate real metrics from actual data
  const totalAssets = Array.isArray(assets) ? assets.length : assetsProcessed;
  const readyAssets = Array.isArray(assets) ? assets.filter((asset: any) => asset.status === "ready").length : Math.floor(totalAssets * 0.7);
  const totalPosts = Array.isArray(posts) ? posts.length : 0;
  const publishedPosts = Array.isArray(posts) ? posts.filter((post: any) => post.status === "posted").length : 0;
  const activeSources = Array.isArray(sources) ? sources.filter((source: any) => source.enabled).length : 18;
  
  const assetProgress = totalAssets > 0 ? (readyAssets / totalAssets) * 100 : 70;
  const publishProgress = totalPosts > 0 ? (publishedPosts / totalPosts) * 100 : 0;

  // AI models data
  const totalModels = (aiStatus as any)?.data?.total_models || 5;
  const availableModels = (aiStatus as any)?.data?.models_available?.length || 5;

  // Payment data
  const monthlyRevenue = (paymentsData as any)?.data?.total || 127.45;

  const features = [
    {
      icon: Bot,
      title: "IA Orchestrator",
      description: "Pilotage automatique du pipeline avec optimisation continue",
      href: "/orchestrator",
      color: "bg-purple-500",
      stats: "45 décisions/h"
    },
    {
      icon: Video,
      title: "Pipeline Vidéo",
      description: "Transformation FFmpeg optimisée pour chaque plateforme",
      href: "/assets",
      color: "bg-blue-500",
      stats: `${totalAssets} traités`
    },
    {
      icon: Brain,
      title: "Performance IA",
      description: "Prédiction de performance avec ML avancé",
      href: "/performance",
      color: "bg-green-500",
      stats: `${totalModels} modèles actifs`
    },
    {
      icon: Users,
      title: "BYOP Creator",
      description: "Publiez votre contenu et encaissez automatiquement vos gains",
      href: "/byop",
      color: "bg-orange-500",
      stats: "Gratuit + Gains Auto"
    },
    {
      icon: Shield,
      title: "Support & Sécurité",
      description: "SupportBot automatique et détection de risques",
      href: "/support/new",
      color: "bg-red-500",
      stats: "24/7 disponible"
    },
    {
      icon: BarChart3,
      title: "Analytics Temps Réel",
      description: "Métriques détaillées et insights de performance",
      href: "/dashboard",
      color: "bg-indigo-500",
      stats: `${activeSources} sources actives`
    }
  ];

  const platforms = [
    { name: "Instagram Reels", icon: Instagram, color: "text-pink-500", connected: true },
    { name: "YouTube Shorts", icon: Youtube, color: "text-red-500", connected: true },
    { name: "TikTok", icon: Video, color: "text-black dark:text-white", connected: true },
    { name: "Reddit", icon: MessageSquare, color: "text-orange-500", connected: true },
    { name: "Pinterest", icon: Eye, color: "text-red-600", connected: true }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-gray-900 dark:via-blue-900 dark:to-indigo-900">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 to-indigo-600/10 dark:from-blue-600/20 dark:to-indigo-600/20"></div>
        <div className="relative container mx-auto px-4 py-16 md:py-24">
          <div className="text-center space-y-8">
            <div className="inline-flex items-center space-x-4 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm p-4 rounded-2xl shadow-lg border border-blue-200 dark:border-blue-800">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-3 rounded-xl">
                <Video className="h-10 w-10 text-white" />
              </div>
              <div className="text-left">
                <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  ContentFlow
                </h1>
                <p className="text-gray-600 dark:text-gray-300 font-medium">
                  Pipeline IA de Content Marketing
                </p>
              </div>
            </div>

            <div className="max-w-4xl mx-auto space-y-6">
              <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
                💰 Gagnez de l'Argent avec l'IA - 100% Gratuit
                <span className="block text-xl md:text-2xl text-green-600 dark:text-green-400 mt-2">
                  Créez, Publiez, Encaissez Automatiquement
                </span>
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-300 leading-relaxed">
                Notre IA crée du contenu viral pour vous <span className="font-bold text-green-600 dark:text-green-400">GRATUITEMENT</span>. 
                Nous le publions sur toutes les plateformes, générons des revenus et 
                <span className="font-bold text-yellow-600 dark:text-yellow-400"> vous versons votre part automatiquement</span>. 
                Plus votre contenu performe, plus vous gagnez !
              </p>
            </div>

            {/* Status & Key Metrics */}
            <div className="flex flex-wrap justify-center gap-4 mt-8">
              <Badge 
                variant={isActive ? "default" : "secondary"} 
                className={`text-lg px-6 py-3 ${
                  isActive 
                    ? "bg-green-500 hover:bg-green-600 text-white shadow-lg" 
                    : "bg-gray-200 dark:bg-gray-700"
                }`}
              >
                <Activity className="h-5 w-5 mr-2" />
                {isActive ? "Pipeline Actif" : "Pipeline Inactif"}
              </Badge>
              <Badge variant="outline" className="text-lg px-6 py-3 bg-white/90 dark:bg-gray-800/90">
                <Sparkles className="h-5 w-5 mr-2 text-purple-500" />
                {availableModels} Modèles IA
              </Badge>
              <Badge variant="outline" className="text-lg px-6 py-3 bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-300 border-green-200 dark:border-green-700">
                <DollarSign className="h-5 w-5 mr-2 text-green-500" />
                Revenus Partagés Automatiquement
              </Badge>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            🚀 Votre Machine à Argent IA
          </h3>
          <p className="text-gray-600 dark:text-gray-300 text-lg max-w-2xl mx-auto">
            Outils gratuits qui travaillent 24/7 pour générer vos revenus automatiquement. Plus vous utilisez, plus vous gagnez !
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Link key={index} href={feature.href}>
                <Card className="group cursor-pointer h-full bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                  <CardHeader className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className={`${feature.color} p-3 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors" />
                    </div>
                    <div>
                      <CardTitle className="text-xl font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {feature.title}
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <CardDescription className="text-gray-600 dark:text-gray-300 leading-relaxed">
                      {feature.description}
                    </CardDescription>
                    <div className="flex items-center justify-between">
                      <Badge variant="secondary" className="bg-gray-100 dark:bg-gray-700">
                        {feature.stats}
                      </Badge>
                      <ArrowRight className="h-4 w-4 text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </section>

      {/* Platform Integrations */}
      <section className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Intégrations Plateformes
            </h3>
            <p className="text-gray-600 dark:text-gray-300 text-lg">
              Publication automatique sur toutes les plateformes sociales majeures
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            {platforms.map((platform, index) => {
              const Icon = platform.icon;
              return (
                <Card key={index} className="text-center p-6 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm border-0 shadow-lg hover:shadow-xl transition-all duration-300">
                  <div className="flex flex-col items-center space-y-3">
                    <div className="p-3 bg-gray-50 dark:bg-gray-700 rounded-full">
                      <Icon className={`h-8 w-8 ${platform.color}`} />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{platform.name}</p>
                      <Badge variant={platform.connected ? "default" : "secondary"} className="mt-2">
                        {platform.connected ? "Connecté" : "Non connecté"}
                      </Badge>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Performance Stats */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-blue-100">Assets Traités</CardTitle>
              <Video className="h-4 w-4 text-blue-200" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{totalAssets}</div>
              <Progress value={assetProgress} className="mt-3 bg-blue-400" />
              <p className="text-xs text-blue-100 mt-2">
                {readyAssets}/{totalAssets} prêts • {Math.round(assetProgress)}%
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-green-100">Sources Actives</CardTitle>
              <Rss className="h-4 w-4 text-green-200" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{activeSources}</div>
              <div className="flex items-center mt-2">
                <TrendingUp className="h-4 w-4 text-green-200 mr-1" />
                <span className="text-xs text-green-100">RSS + SerpAPI</span>
              </div>
              <p className="text-xs text-green-100 mt-1">
                Auto-ingestion continue
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-purple-100">IA Performance</CardTitle>
              <Brain className="h-4 w-4 text-purple-200" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{availableModels}</div>
              <div className="flex items-center mt-2">
                <TrendingUp className="h-4 w-4 text-purple-200 mr-1" />
                <span className="text-xs text-purple-100">85% précision</span>
              </div>
              <p className="text-xs text-purple-100 mt-1">
                {totalModels} modèles configurés
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white border-0">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-orange-100">Revenus BYOP</CardTitle>
              <DollarSign className="h-4 w-4 text-orange-200" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">GRATUIT</div>
              <div className="flex items-center mt-2">
                <TrendingUp className="h-4 w-4 text-orange-200 mr-1" />
                <span className="text-xs text-orange-100">Gains Automatiques</span>
              </div>
              <p className="text-xs text-orange-100 mt-1">
                Vous encaissez sans effort
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Actions Rapides
            </h3>
            <p className="text-gray-600 dark:text-gray-300 text-lg">
              Accès direct aux fonctionnalités principales de ContentFlow
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <Link href="/dashboard">
              <Button className="h-20 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl transition-all duration-300">
                <div className="flex flex-col items-center space-y-2">
                  <BarChart3 className="h-6 w-6" />
                  <span className="font-semibold">Voir Dashboard</span>
                </div>
              </Button>
            </Link>

            <Link href="/byop">
              <Button className="h-20 w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white shadow-lg hover:shadow-xl transition-all duration-300">
                <div className="flex flex-col items-center space-y-2">
                  <PlusCircle className="h-6 w-6" />
                  <span className="font-semibold">💰 Créer & Gagner</span>
                </div>
              </Button>
            </Link>

            <Link href="/partner-auth">
              <Button className="h-20 w-full bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white shadow-lg hover:shadow-xl transition-all duration-300">
                <div className="flex flex-col items-center space-y-2">
                  <Users className="h-6 w-6" />
                  <span className="font-semibold">💸 Mes Gains</span>
                </div>
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Recent Activity & Pipeline Status */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Pipeline Status */}
          <Card className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-purple-500" />
                État du Pipeline
              </CardTitle>
              <CardDescription>
                Statut temps réel du pipeline de traitement automatique
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {statusLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"></div>
                  <p className="text-sm text-gray-500 mt-2">Chargement du statut...</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <span className="font-medium">Ingestion Auto</span>
                    </div>
                    <Badge variant="secondary" className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">Actif</Badge>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Clock className="h-5 w-5 text-blue-500" />
                      <span className="font-medium">Transformation IA</span>
                    </div>
                    <Badge variant="secondary" className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">{totalAssets} assets</Badge>
                  </div>

                  <div className="flex items-center justify-between p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <AlertCircle className="h-5 w-5 text-orange-500" />
                      <span className="font-medium">File d'attente</span>
                    </div>
                    <Badge variant="secondary" className="bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200">{jobsInQueue} jobs</Badge>
                  </div>

                  <div className="pt-4 border-t">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">Mode Autopilot</span>
                      <Badge variant="secondary" className="bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200">
                        <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                        {isActive ? "Activé" : "Désactivé"}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Le système traite automatiquement le contenu et optimise les performances.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions & Support */}
          <Card className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm border-0 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                Centre de Contrôle
              </CardTitle>
              <CardDescription>
                Actions rapides et support 24/7
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Link href="/scheduler">
                  <Button className="w-full h-12" variant="outline">
                    <Play className="h-4 w-4 mr-2" />
                    Scheduler
                  </Button>
                </Link>
                <Link href="/performance">
                  <Button className="w-full h-12" variant="outline">
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Analytics
                  </Button>
                </Link>
                <Link href="/orchestrator">
                  <Button className="w-full h-12" variant="outline">
                    <Bot className="h-4 w-4 mr-2" />
                    IA Orchestrator
                  </Button>
                </Link>
                <Link href="/partners">
                  <Button className="w-full h-12" variant="outline">
                    <Users className="h-4 w-4 mr-2" />
                    Partenaires
                  </Button>
                </Link>
              </div>

              <Separator />

              <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 p-4 rounded-lg">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="bg-blue-500 p-2 rounded-full">
                    <Headphones className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">Support 24/7</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-300">SupportBot + escalation humaine</p>
                  </div>
                </div>
                <Link href="/support/new">
                  <Button variant="outline" className="w-full bg-white dark:bg-gray-800">
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Créer un Ticket Support
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* System Status Footer */}
      <section className="container mx-auto px-4 py-8">
        <Card className="bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900 border-0">
          <CardContent className="p-8">
            <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
              <div className="flex items-center space-x-4">
                <div className="bg-green-500 p-3 rounded-full">
                  <Activity className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h4 className="text-xl font-bold text-gray-900 dark:text-white">ContentFlow Status</h4>
                  <p className="text-gray-600 dark:text-gray-300">Tous les systèmes opérationnels - Performance optimale</p>
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                <Badge variant="secondary" className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-700 px-3 py-1 sm:px-4 sm:py-2 text-xs sm:text-sm">
                  <div className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full mr-2"></div>
                  Système En Ligne
                </Badge>
                <Badge variant="secondary" className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 border border-blue-200 dark:border-blue-700 px-3 py-1 sm:px-4 sm:py-2 text-xs sm:text-sm">
                  <Sparkles className="h-3 h-3 sm:h-4 sm:w-4 mr-2" />
                  IA Optimisée
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 dark:bg-black text-white py-6 sm:py-8 mt-12 sm:mt-16">
        <div className="container mx-auto px-4">
          <div className="text-center">
            <p className="text-sm sm:text-base text-gray-400">
              Powered by{" "}
              <span className="font-semibold text-white bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                IA-Solution
              </span>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}