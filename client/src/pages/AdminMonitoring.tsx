import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  TrendingUp, 
  MousePointer, 
  Euro, 
  Users, 
  Shield, 
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw
} from 'lucide-react';

interface AnalyticsData {
  clicks_7d: number;
  conv_7d: number;
  rev_7d: number;
  epc_7d: number;
  available: number;
  reserved: number;
  paid: number;
  pending: number;
  approved: number;
  posted: number;
  failed: number;
  holds: number;
  postbacks_24h: number;
  partners_active: number;
  offer: {
    headline_cpc: number;
    epc_7d: number;
    terms: { mode: string };
  };
}

export default function AdminMonitoring() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [adminSecret] = useState('admin123'); // In production, this would be from environment

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch('/admin/monitoring/api', {
        headers: {
          'x-admin-secret': adminSecret
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setAnalytics(data.data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-center h-96">
            <div className="flex items-center space-x-2">
              <RefreshCw className="h-6 w-6 animate-spin text-blue-600" />
              <span className="text-lg text-gray-600 dark:text-gray-300">Chargement du monitoring...</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
        <div className="max-w-6xl mx-auto">
          <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
            <CardHeader>
              <CardTitle className="text-red-800 dark:text-red-200">Erreur de connexion</CardTitle>
              <CardDescription className="text-red-600 dark:text-red-300">
                Impossible de charger les données de monitoring: {error}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={fetchAnalytics} variant="outline" className="text-red-700 border-red-300">
                <RefreshCw className="h-4 w-4 mr-2" />
                Réessayer
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  const totalAssignments = analytics.pending + analytics.approved + analytics.posted + analytics.failed;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center space-x-3 bg-white dark:bg-gray-800 px-6 py-3 rounded-full shadow-lg">
            <Activity className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">ContentFlow Admin</h1>
          </div>
          <p className="text-gray-600 dark:text-gray-300 text-lg">
            Tableau de bord en temps réel - Performance et santé de la plateforme
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>Dernière maj: {lastUpdate.toLocaleTimeString('fr-FR')}</span>
            </div>
            <Badge variant="secondary" className="text-xs">
              {analytics.offer.terms.mode.toUpperCase()}
            </Badge>
            <Button 
              onClick={fetchAnalytics} 
              size="sm" 
              variant="ghost"
              disabled={loading}
              data-testid="button-refresh-analytics"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </div>

        {/* Revenue Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-900/10 border-green-200 dark:border-green-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-green-700 dark:text-green-300 flex items-center">
                <Euro className="h-4 w-4 mr-2" />
                Revenus 7 jours
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-900 dark:text-green-100" data-testid="text-revenue-7d">
                €{analytics.rev_7d.toFixed(2)}
              </div>
              <p className="text-sm text-green-600 dark:text-green-400">
                EPC: €{analytics.epc_7d.toFixed(3)}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-blue-50 to-cyan-100 dark:from-blue-900/20 dark:to-cyan-900/10 border-blue-200 dark:border-blue-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-blue-700 dark:text-blue-300 flex items-center">
                <MousePointer className="h-4 w-4 mr-2" />
                Clics 7 jours
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-900 dark:text-blue-100" data-testid="text-clicks-7d">
                {analytics.clicks_7d.toLocaleString()}
              </div>
              <p className="text-sm text-blue-600 dark:text-blue-400">
                Conversions: {analytics.conv_7d}
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-900/10 border-purple-200 dark:border-purple-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-purple-700 dark:text-purple-300 flex items-center">
                <TrendingUp className="h-4 w-4 mr-2" />
                CPC Offre
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-900 dark:text-purple-100" data-testid="text-cpc-offer">
                €{analytics.offer.headline_cpc.toFixed(2)}
              </div>
              <p className="text-sm text-purple-600 dark:text-purple-400">par clic</p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-orange-50 to-amber-100 dark:from-orange-900/20 dark:to-amber-900/10 border-orange-200 dark:border-orange-800">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-orange-700 dark:text-orange-300 flex items-center">
                <Users className="h-4 w-4 mr-2" />
                Partenaires Actifs
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-900 dark:text-orange-100" data-testid="text-partners-active">
                {analytics.partners_active}
              </div>
              <p className="text-sm text-orange-600 dark:text-orange-400">7 derniers jours</p>
            </CardContent>
          </Card>
        </div>

        {/* Financial Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Euro className="h-5 w-5 mr-2 text-green-600" />
              Gestion des Paiements
            </CardTitle>
            <CardDescription>Aperçu des finances partenaires</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div className="text-2xl font-bold text-green-700 dark:text-green-300" data-testid="text-available-balance">
                  €{analytics.available.toFixed(2)}
                </div>
                <p className="text-sm text-green-600 dark:text-green-400">Disponible</p>
              </div>
              <div className="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                <div className="text-2xl font-bold text-yellow-700 dark:text-yellow-300" data-testid="text-reserved-balance">
                  €{analytics.reserved.toFixed(2)}
                </div>
                <p className="text-sm text-yellow-600 dark:text-yellow-400">Réservé</p>
              </div>
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="text-2xl font-bold text-blue-700 dark:text-blue-300" data-testid="text-paid-balance">
                  €{analytics.paid.toFixed(2)}
                </div>
                <p className="text-sm text-blue-600 dark:text-blue-400">Payé</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pipeline Status */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Activity className="h-5 w-5 mr-2 text-blue-600" />
                Pipeline de Publication
              </CardTitle>
              <CardDescription>Statut des assignments en cours</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Total Assignments</span>
                  <Badge variant="secondary" data-testid="badge-total-assignments">{totalAssignments}</Badge>
                </div>
                <Separator />
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex justify-between">
                    <span className="flex items-center">
                      <Clock className="h-4 w-4 mr-1 text-yellow-500" />
                      Pending
                    </span>
                    <Badge variant="outline" data-testid="badge-pending">{analytics.pending}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="flex items-center">
                      <CheckCircle className="h-4 w-4 mr-1 text-green-500" />
                      Approved
                    </span>
                    <Badge variant="outline" data-testid="badge-approved">{analytics.approved}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="flex items-center">
                      <TrendingUp className="h-4 w-4 mr-1 text-blue-500" />
                      Posted
                    </span>
                    <Badge variant="outline" data-testid="badge-posted">{analytics.posted}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="flex items-center">
                      <XCircle className="h-4 w-4 mr-1 text-red-500" />
                      Failed
                    </span>
                    <Badge variant="outline" data-testid="badge-failed">{analytics.failed}</Badge>
                  </div>
                </div>

                {totalAssignments === 0 && (
                  <div className="text-center p-4 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <Activity className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm">Aucune activité de publication</p>
                    <p className="text-xs mt-1">En attente de soumissions partenaires</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="h-5 w-5 mr-2 text-red-600" />
                Sécurité & Surveillance
              </CardTitle>
              <CardDescription>Monitoring des risques et anomalies</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium flex items-center">
                    <AlertTriangle className="h-4 w-4 mr-2 text-yellow-500" />
                    Holds Actifs
                  </span>
                  <Badge 
                    variant={analytics.holds > 0 ? "destructive" : "secondary"}
                    data-testid="badge-holds"
                  >
                    {analytics.holds}
                  </Badge>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium flex items-center">
                    <Activity className="h-4 w-4 mr-2 text-blue-500" />
                    Postbacks 24h
                  </span>
                  <Badge variant="outline" data-testid="badge-postbacks">{analytics.postbacks_24h}</Badge>
                </div>

                <Separator />

                <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-lg font-semibold text-green-700 dark:text-green-300">
                    {analytics.holds === 0 ? '✅ Système Sain' : '⚠️ Surveillance Active'}
                  </div>
                  <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                    {analytics.holds === 0 ? 'Aucune anomalie détectée' : `${analytics.holds} partenaire(s) sous surveillance`}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Zero State Message */}
        {analytics.rev_7d === 0 && analytics.clicks_7d === 0 && (
          <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
            <CardContent className="text-center p-8">
              <Activity className="h-16 w-16 mx-auto mb-4 text-blue-500 opacity-50" />
              <h3 className="text-lg font-semibold text-blue-800 dark:text-blue-200 mb-2">
                Interface de Monitoring Prête
              </h3>
              <p className="text-blue-600 dark:text-blue-300 mb-4">
                Les données apparaîtront ici dès que les partenaires commenceront à utiliser la plateforme BYOP
              </p>
              <div className="flex justify-center space-x-4">
                <Button variant="outline" size="sm" asChild>
                  <a href="/byop" data-testid="link-byop-interface">
                    Interface BYOP
                  </a>
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <a href="/partner-profile" data-testid="link-partner-profile">
                    Profil Partenaire
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}