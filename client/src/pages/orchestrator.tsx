import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { Bot, Brain, Zap, Activity, Settings, PlayCircle, PauseCircle, BarChart3 } from "lucide-react";

export default function OrchestratorPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [isDryRun, setIsDryRun] = useState(true);

  // Requête statut AI Orchestrator
  const { data: status } = useQuery({
    queryKey: ["/api/ai/orchestrator/status"],
    refetchInterval: 5000,
  });

  // Requête KPIs
  const { data: kpis } = useQuery({
    queryKey: ["/api/ai/kpis"],
    refetchInterval: 10000,
  });

  // Requête historique actions
  const { data: actionHistory } = useQuery({
    queryKey: ["/api/ai/actions/history"],
    refetchInterval: 5000,
  });

  // Mutation pour déclencher un tick
  const tickMutation = useMutation({
    mutationFn: async (dry: boolean) => {
      const response = await fetch(`/api/ai/tick?dry=${dry}`, { 
        method: "POST" 
      });
      return response.json();
    },
    onSuccess: (data) => {
      if (data.ok) {
        toast({
          title: "Tick AI exécuté",
          description: `${data.executed?.length || 0} actions exécutées`,
        });
      } else {
        toast({
          title: "Erreur tick AI",
          description: data.error || "Erreur inconnue",
          variant: "destructive",
        });
      }
      queryClient.invalidateQueries({ queryKey: ["/api/ai"] });
    },
  });

  const orchestratorStatus = (status as any)?.data || {};
  const globalKpis = (kpis as any)?.global || {};
  const actions = actionHistory || [];

  return (
    <div className="container mx-auto py-6 space-y-6 bg-gray-50 dark:bg-gray-900 min-h-screen transition-colors duration-300 px-4 md:px-6">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between space-y-4 md:space-y-0">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold flex items-center space-x-2 text-gray-900 dark:text-white">
            <Bot className="w-6 h-6 md:w-8 md:h-8 text-blue-600 dark:text-blue-400" />
            <span>AI Orchestrator</span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm md:text-base">
            Pipeline automatisé avec intelligence artificielle et optimisation des revenus
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <Badge variant={orchestratorStatus.autopilot_enabled ? "default" : "secondary"}>
            {orchestratorStatus.autopilot_enabled ? "✅ Activé" : "⏸️ Désactivé"}
          </Badge>
          {orchestratorStatus.dry_run_mode && (
            <Badge variant="outline">Mode Test</Badge>
          )}
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Status IA</p>
                <p className="text-2xl font-bold text-blue-600" data-testid="text-ai-status">
                  {orchestratorStatus.health === "ok" ? "Opérationnel" : "Problème"}
                </p>
              </div>
              <Activity className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">CTR Global</p>
                <p className="text-2xl font-bold text-green-600" data-testid="text-global-ctr">
                  {(globalKpis.ctr * 100 || 0).toFixed(2)}%
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Revenus</p>
                <p className="text-2xl font-bold text-purple-600" data-testid="text-revenue">
                  €{(globalKpis.revenue || 0).toFixed(2)}
                </p>
              </div>
              <Zap className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Intervalle</p>
                <p className="text-2xl font-bold text-orange-600" data-testid="text-interval">
                  {orchestratorStatus.tick_interval_minutes || 10}min
                </p>
              </div>
              <Settings className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <PlayCircle className="w-5 h-5" />
            <span>Contrôles IA</span>
          </CardTitle>
          <CardDescription>
            Déclenchez manuellement l'intelligence artificielle ou configurez le mode
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Mode Test (Dry Run)</p>
              <p className="text-sm text-muted-foreground">
                Simule les actions sans les exécuter réellement
              </p>
            </div>
            <Switch
              checked={isDryRun}
              onCheckedChange={setIsDryRun}
              data-testid="switch-dry-run"
            />
          </div>

          <Separator />

          <div className="flex space-x-2">
            <Button
              onClick={() => tickMutation.mutate(isDryRun)}
              disabled={tickMutation.isPending}
              className="flex items-center space-x-2"
              data-testid="button-execute-tick"
            >
              <Brain className="w-4 h-4" />
              <span>
                {tickMutation.isPending ? "Exécution..." : "Exécuter Tick IA"}
              </span>
            </Button>

            <Button
              variant="outline"
              onClick={() => tickMutation.mutate(true)}
              disabled={tickMutation.isPending}
              data-testid="button-dry-run-tick"
            >
              Simulation Seulement
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Historique des Actions IA</CardTitle>
          <CardDescription>
            Dernières décisions et actions de l'orchestrateur
          </CardDescription>
        </CardHeader>
        <CardContent>
          {(actions as any[])?.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Aucune action IA enregistrée</p>
              <p className="text-sm">Déclenchez un tick pour voir l'activité</p>
            </div>
          ) : (
            <div className="space-y-3">
              {(actions as any[])?.slice(0, 10).map((action: any) => (
                <div
                  key={action.id}
                  className="flex items-center justify-between p-3 border rounded-lg"
                  data-testid={`action-${action.kind}`}
                >
                  <div>
                    <p className="font-medium">{action.kind}</p>
                    <p className="text-sm text-muted-foreground">
                      Score: {action.decision_score?.toFixed(3)} | 
                      {action.target && ` Target: ${action.target}`}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge 
                      variant={action.success ? "default" : action.executed ? "destructive" : "secondary"}
                    >
                      {action.success ? "✅ Succès" : action.executed ? "❌ Échec" : "⏳ En attente"}
                    </Badge>
                    <p className="text-xs text-muted-foreground">
                      {new Date(action.tick_ts).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* KPIs Detail */}
      <Card>
        <CardHeader>
          <CardTitle>Métriques Détaillées</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold">{globalKpis.views || 0}</p>
              <p className="text-sm text-muted-foreground">Vues Totales</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{globalKpis.clicks || 0}</p>
              <p className="text-sm text-muted-foreground">Clics Totaux</p>
            </div>
            <div>
              <p className="text-2xl font-bold">€{(globalKpis.epc || 0).toFixed(3)}</p>
              <p className="text-sm text-muted-foreground">EPC Moyen</p>
            </div>
            <div>
              <p className="text-2xl font-bold">{orchestratorStatus.objective || "revenue_ctr_safe"}</p>
              <p className="text-sm text-muted-foreground">Objectif IA</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}