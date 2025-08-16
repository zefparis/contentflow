import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Mail, CheckCircle, Clock, ArrowLeft } from "lucide-react";

interface AuthState {
  step: 'email' | 'verification' | 'success';
  email: string;
  verificationSent: boolean;
}

export default function PartnerAuthPage() {
  const [authState, setAuthState] = useState<AuthState>({
    step: 'email',
    email: '',
    verificationSent: false
  });
  const { toast } = useToast();

  // Check if device is already verified and authenticated
  const isDeviceVerified = () => {
    return typeof window !== 'undefined' && document && document.cookie.includes('device_verified=true');
  };

  const isAuthenticated = () => {
    return typeof window !== 'undefined' && document &&
           document.cookie.includes('partner_id=') && isDeviceVerified();
  };

  // Auto-redirect if already authenticated
  if (isAuthenticated()) {
    console.log('Already authenticated, redirecting to BYOP...');
    window.location.href = '/byop';
    return null;
  }

  const sendMagicLinkMutation = useMutation({
    mutationFn: async (email: string) => {
      const response = await fetch("/api/auth/magic-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return response.json();
    },
    onSuccess: () => {
      setAuthState(prev => ({ ...prev, step: 'verification', verificationSent: true }));
      toast({
        title: "Lien envoyé !",
        description: "Vérifiez votre email et cliquez sur le lien de connexion."
      });
    },
    onError: (error: Error) => {
      toast({
        title: "Erreur",
        description: "Impossible d'envoyer le lien de connexion. Réessayez.",
        variant: "destructive"
      });
    }
  });

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const email = formData.get('email') as string;
    
    if (!email || !email.includes('@')) {
      toast({
        title: "Email invalide",
        description: "Veuillez saisir une adresse email valide.",
        variant: "destructive"
      });
      return;
    }

    setAuthState(prev => ({ ...prev, email }));
    sendMagicLinkMutation.mutate(email);
  };

  const handleResendLink = () => {
    sendMagicLinkMutation.mutate(authState.email);
  };

  const demoLoginMutation = useMutation({
    mutationFn: async (email: string) => {
      const response = await fetch("/api/auth/demo-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return response.json();
    },
    onSuccess: () => {
      toast({
        title: "Connexion réussie !",
        description: "Redirection vers votre profil partenaire..."
      });
      setTimeout(() => {
        window.location.href = '/partner-profile';
      }, 1000);
    },
    onError: (error: Error) => {
      toast({
        title: "Erreur de connexion",
        description: "Impossible de se connecter en mode demo.",
        variant: "destructive"
      });
    }
  });

  const handleDemoLogin = (email: string) => {
    demoLoginMutation.mutate(email);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card className="bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl text-gray-900 dark:text-white">
              Connexion Partenaire
            </CardTitle>
            <CardDescription className="text-gray-600 dark:text-gray-400">
              {authState.step === 'email' && "Accédez à votre espace partenaire BYOP"}
              {authState.step === 'verification' && "Vérification de votre email"}
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {authState.step === 'email' && (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="email" className="text-gray-900 dark:text-white">
                    Email partenaire
                  </Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="votre@email.com"
                    required
                    className="bg-gray-50 dark:bg-gray-700 border-gray-300 dark:border-gray-600"
                    data-testid="input-email"
                  />
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  disabled={sendMagicLinkMutation.isPending}
                  data-testid="button-send-magic-link"
                >
                  {sendMagicLinkMutation.isPending ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      Envoi en cours...
                    </>
                  ) : (
                    <>
                      <Mail className="w-4 h-4 mr-2" />
                      Recevoir le lien de connexion
                    </>
                  )}
                </Button>
                
                <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  Un lien de connexion sécurisé sera envoyé à votre email.
                  Aucun mot de passe requis.
                </div>
                
                {/* Demo login for development */}
                {process.env.NODE_ENV === 'development' && (
                  <div className="border-t pt-4">
                    <Button
                      variant="outline"
                      onClick={() => handleDemoLogin('demo@partner.com')}
                      className="w-full text-xs"
                      data-testid="button-demo-login"
                    >
                      🚀 Demo Login (dev only)
                    </Button>
                  </div>
                )}
              </form>
            )}

            {authState.step === 'verification' && (
              <div className="text-center space-y-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900 rounded-lg">
                  <CheckCircle className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <h3 className="font-medium text-blue-900 dark:text-blue-100">
                    Email envoyé !
                  </h3>
                  <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                    Vérifiez votre boîte email <strong>{authState.email}</strong>
                  </p>
                </div>
                
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <p>• Cliquez sur le lien dans l'email pour vous connecter</p>
                  <p>• Le lien est valide pendant 15 minutes</p>
                  <p>• Vérifiez aussi vos spams</p>
                </div>
                
                <div className="flex flex-col space-y-2">
                  <Button
                    variant="outline"
                    onClick={handleResendLink}
                    disabled={sendMagicLinkMutation.isPending}
                    data-testid="button-resend-link"
                  >
                    {sendMagicLinkMutation.isPending ? "Renvoi..." : "Renvoyer le lien"}
                  </Button>
                  
                  <Button
                    variant="ghost"
                    onClick={() => setAuthState({ step: 'email', email: '', verificationSent: false })}
                    className="text-gray-600 dark:text-gray-400"
                    data-testid="button-back"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Utiliser un autre email
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        <div className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
          <p>Espace réservé aux partenaires ContentFlow</p>
          <p>Pour devenir partenaire, contactez-nous.</p>
        </div>
      </div>
    </div>
  );
}