import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Users, TrendingUp, DollarSign, Award, Mail, ArrowRight, Star } from "lucide-react";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

export default function Partners() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setIsSubmitting(true);
    
    try {
      const response = await fetch('/partner/magic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `email=${encodeURIComponent(email)}`
      });
      
      if (response.ok) {
        toast({
          title: "Lien d'accès envoyé !",
          description: "Vérifiez votre email pour accéder au portail partenaire",
        });
        setEmail("");
        
        // En développement, ouvrir directement la page de confirmation
        if (response.headers.get('content-type')?.includes('text/html')) {
          const htmlContent = await response.text();
          const newWindow = window.open('', '_blank');
          if (newWindow) {
            newWindow.document.write(htmlContent);
            newWindow.document.close();
          }
        }
      } else {
        throw new Error('Erreur lors de l\'inscription');
      }
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible d'envoyer le lien d'accès",
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 transition-colors duration-300">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="container mx-auto px-4 py-8 md:py-16">
          <div className="text-center max-w-4xl mx-auto">
            <div className="flex items-center justify-center mb-6">
              <Users className="w-8 h-8 md:w-12 md:h-12 text-blue-600 dark:text-blue-400 mr-3" />
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-gray-900 dark:text-white">
                Programme Partenaires
              </h1>
            </div>
            
            <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300 mb-8 px-4">
              Monétisez votre audience avec du contenu automatisé par IA. 
              Gagnez des revenus sans créer de contenu.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-12 px-4">
              <Badge className="bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-sm md:text-lg px-3 md:px-4 py-2 border border-green-200 dark:border-green-700">
                <DollarSign className="w-3 h-3 md:w-4 md:h-4 mr-1" />
                jusqu'à €0.12 par clic
              </Badge>
              <Badge className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-sm md:text-lg px-3 md:px-4 py-2 border border-blue-200 dark:border-blue-700">
                <TrendingUp className="w-3 h-3 md:w-4 md:h-4 mr-1" />
                Paiements automatiques
              </Badge>
              <Badge className="bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-sm md:text-lg px-3 md:px-4 py-2 border border-purple-200 dark:border-purple-700">
                <Award className="w-3 h-3 md:w-4 md:h-4 mr-1" />
                Leaderboard gamifié
              </Badge>
            </div>

            {/* Signup Form */}
            <Card className="max-w-md mx-auto bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm shadow-xl border-gray-200 dark:border-gray-700">
              <CardHeader>
                <CardTitle className="text-center flex items-center justify-center text-gray-900 dark:text-white">
                  <Mail className="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" />
                  Rejoindre le programme
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSignup} className="space-y-4">
                  <Input
                    type="email"
                    placeholder="votre@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="text-center"
                    data-testid="input-partner-email"
                  />
                  <Button 
                    type="submit" 
                    className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                    disabled={isSubmitting}
                    data-testid="button-join-partners"
                  >
                    {isSubmitting ? "Envoi..." : "Obtenir un lien d'accès"}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                  
                  {/* Lien demo temporaire en attendant déploiement */}
                  <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg">
                    <p className="text-sm text-blue-800 dark:text-blue-300 mb-2">
                      Aperçu du portail partenaire :
                    </p>
                    <Button 
                      type="button" 
                      variant="outline" 
                      className="w-full border-blue-300 dark:border-blue-600 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-800/50"
                      onClick={() => window.open('/partner/demo-portal', '_blank')}
                    >
                      Voir le portail partenaire
                    </Button>
                    <p className="text-xs text-blue-600 dark:text-blue-400 mt-2">
                      Interface complète avec statistiques et fonctionnalités
                    </p>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900 dark:text-white">
          Comment ça marche ?
        </h2>
        
        <div className="grid md:grid-cols-3 gap-8">
          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <Users className="w-12 h-12 text-blue-600 mx-auto mb-4" />
              <CardTitle>1. Inscription simple</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-300">
                Inscrivez-vous en 30 secondes avec votre email. 
                Accès instantané au portail partenaire.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <TrendingUp className="w-12 h-12 text-green-600 mx-auto mb-4" />
              <CardTitle>2. Partage automatisé</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-300">
                Notre IA créé et publie du contenu optimisé 
                sur vos réseaux sociaux automatiquement.
              </p>
            </CardContent>
          </Card>

          <Card className="text-center hover:shadow-lg transition-shadow">
            <CardHeader>
              <DollarSign className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
              <CardTitle>3. Revenus passifs</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-600 dark:text-gray-300">
                Gagnez €0.20 par clic généré. 
                Retraits à partir de €10 via PayPal ou virement.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm py-16">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">500+</div>
              <div className="text-gray-600 dark:text-gray-300">Partenaires actifs</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600 mb-2">€25,000</div>
              <div className="text-gray-600 dark:text-gray-300">Revenus distribués</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">1.2M</div>
              <div className="text-gray-600 dark:text-gray-300">Clics générés</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-yellow-600 mb-2">98%</div>
              <div className="text-gray-600 dark:text-gray-300">Satisfaction</div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="container mx-auto px-4 py-16 text-center">
        <h2 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">
          Prêt à commencer ?
        </h2>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
          Rejoignez des centaines de partenaires qui génèrent des revenus passifs
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Button 
            size="lg"
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            onClick={() => document.querySelector('[data-testid="input-partner-email"]')?.scrollIntoView({ behavior: 'smooth' })}
            data-testid="button-signup-cta"
          >
            Rejoindre maintenant
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
          
          <Button 
            variant="outline" 
            size="lg"
            onClick={() => window.open('/partners/leaderboard', '_blank')}
            data-testid="button-view-leaderboard"
          >
            <Award className="w-5 h-5 mr-2" />
            Voir le classement
          </Button>
        </div>
      </div>

      {/* Footer Links */}
      <div className="bg-gray-100 dark:bg-gray-800 py-8">
        <div className="container mx-auto px-4 text-center">
          <div className="flex flex-wrap justify-center gap-6 text-sm">
            <a href="/byop" className="text-green-600 hover:underline font-medium" data-testid="link-byop">
              ✍️ Créer un post (BYOP)
            </a>
            <a href="/partners/faq" className="text-blue-600 hover:underline" data-testid="link-faq">
              Questions fréquentes
            </a>
            <a href="/partners/leaderboard" className="text-blue-600 hover:underline" data-testid="link-leaderboard">
              Leaderboard
            </a>
            <a href="/admin/partners/dashboard" className="text-blue-600 hover:underline" data-testid="link-admin">
              Administration
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}