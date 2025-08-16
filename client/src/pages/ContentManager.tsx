import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { apiRequest } from "@/lib/queryClient";
import { Calendar, FileImage, Share, Eye, Edit } from "lucide-react";

interface ContentSubmission {
  id: string;
  partnerId: string;
  userMessage: string;
  generatedTitle: string;
  generatedDescription: string;
  generatedHashtags: string;
  cta: string;
  complianceScore: string;
  qualityScore: string;
  approved: string;
  status: string;
  publishedPlatforms: string[];
  mediaFiles: Array<{
    originalname: string;
    mimetype: string;
    size: number;
    filename?: string;
  }>;
  createdAt: string;
  updatedAt: string;
}

interface SocialConnection {
  id: string;
  partnerId: string;
  platform: string;
  platformUserId: string;
  accountName: string;
  accountUrl: string;
  isActive: string;
  permissions: string[];
  createdAt: string;
}

export default function ContentManager() {
  const [selectedContent, setSelectedContent] = useState<ContentSubmission | null>(null);
  const [publishPlatforms, setPublishPlatforms] = useState<string[]>([]);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // Fetch content submissions
  const { data: contentData, isLoading: contentLoading } = useQuery({
    queryKey: ['/api/content/submissions'],
    staleTime: 30000,
  });

  // Fetch social connections
  const { data: socialData, isLoading: socialLoading } = useQuery({
    queryKey: ['/api/social/connections'],
    staleTime: 30000,
  });

  // Publish content mutation
  const publishMutation = useMutation({
    mutationFn: async ({ contentId, platforms }: { contentId: string; platforms: string[] }) => {
      return await apiRequest("POST", `/api/content/${contentId}/publish`, { platforms });
    },
    onSuccess: (result: any) => {
      const platforms = result?.data?.publishedPlatforms || publishPlatforms;
      toast({
        title: "Publication réussie",
        description: `Votre contenu a été publié sur: ${platforms.map((p: string) => p.charAt(0).toUpperCase() + p.slice(1)).join(', ')}`,
      });
      queryClient.invalidateQueries({ queryKey: ['/api/content/submissions'] });
      setSelectedContent(null);
      setPublishPlatforms([]);
    },
    onError: (error: any) => {
      toast({
        title: "Erreur de publication",
        description: error.message || "Impossible de publier le contenu",
        variant: "destructive",
      });
    },
  });

  const contents = (contentData as any)?.data || [];
  const connections = (socialData as any)?.data || [];
  const availablePlatforms = connections.filter((c: any) => c.isActive === 'true').map((c: any) => c.platform);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'draft':
        return <Badge variant="secondary">Brouillon</Badge>;
      case 'published':
        return <Badge variant="default" className="bg-green-600 hover:bg-green-700">✓ Publié</Badge>;
      case 'processing':
        return <Badge variant="outline" className="border-yellow-500 text-yellow-700">En traitement</Badge>;
      case 'pending_review':
        return <Badge variant="outline" className="border-orange-500 text-orange-700">En attente</Badge>;
      case 'archived':
        return <Badge variant="outline">Archivé</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const handlePublish = () => {
    if (!selectedContent || publishPlatforms.length === 0) return;
    
    publishMutation.mutate({
      contentId: selectedContent.id,
      platforms: publishPlatforms
    });
  };

  if (contentLoading || socialLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin w-8 h-8 border-4 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">Gérer le Contenu</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300">
            Visualisez et publiez vos contenus créés avec l'IA
          </p>
        </div>

        {/* Social Media Status */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Share className="h-5 w-5" />
              Réseaux Sociaux Connectés
            </CardTitle>
            <CardDescription>
              {connections.length === 0 
                ? "Aucun réseau social connecté. Connectez vos comptes pour publier du contenu."
                : `${connections.length} compte(s) connecté(s)`
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 flex-wrap">
              {connections.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 italic">
                  Rendez-vous dans les paramètres pour connecter vos réseaux sociaux
                </p>
              ) : (
                connections.map((conn: any) => (
                  <Badge key={conn.id} variant="outline" className="flex items-center gap-1">
                    {conn.platform.charAt(0).toUpperCase() + conn.platform.slice(1)}
                    {conn.accountName && ` - ${conn.accountName}`}
                  </Badge>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Content Sections */}
        <div className="space-y-8">
          {/* Published Content Section */}
          {contents.filter((c: ContentSubmission) => c.status === 'published').length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Badge variant="default" className="bg-green-600">
                  {contents.filter((c: ContentSubmission) => c.status === 'published').length}
                </Badge>
                Contenu Publié
              </h2>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {contents.filter((c: ContentSubmission) => c.status === 'published').map((content: ContentSubmission) => (
                  <Card key={content.id} className="overflow-hidden hover:shadow-lg transition-shadow border-green-200">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg line-clamp-2 mb-2">
                            {content.generatedTitle || "Titre généré par l'IA"}
                          </CardTitle>
                          <Badge variant="default" className="bg-green-600">✓ Publié</Badge>
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent className="pb-3">
                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-2">
                        {content.generatedDescription || "Description générée par l'IA"}
                      </p>
                      
                      {/* Show published platforms */}
                      {content.publishedPlatforms && content.publishedPlatforms.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Publié sur:</p>
                          <div className="flex flex-wrap gap-1">
                            {content.publishedPlatforms.map((platform: string, index: number) => (
                              <Badge key={index} variant="secondary" className="text-xs bg-blue-100 text-blue-800">
                                {platform.charAt(0).toUpperCase() + platform.slice(1)}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Display uploaded images for published content */}
                      {content.mediaFiles && content.mediaFiles.length > 0 && (
                        <div className="mb-3">
                          <div className="flex flex-wrap gap-2">
                            {content.mediaFiles.slice(0, 2).map((file: any, index: number) => {
                              // Support pour différents formats de données de fichiers
                              const fileName = typeof file === 'string' ? file : (file.filename || file.originalname);
                              const mimeType = typeof file === 'string' ? (file.includes('.jpg') || file.includes('.jpeg') ? 'image/jpeg' : 
                                                                           file.includes('.png') ? 'image/png' :
                                                                           file.includes('.gif') ? 'image/gif' :
                                                                           file.includes('.mp4') ? 'video/mp4' :
                                                                           file.includes('.mp3') ? 'audio/mp3' : 'unknown') : file.mimetype;
                              const originalName = typeof file === 'string' ? file : file.originalname;
                              
                              return (
                                <div key={index} className="relative">
                                  {mimeType?.startsWith('image/') ? (
                                    <img 
                                      src={`/api/media/${fileName}`}
                                      alt={`Média ${index + 1}`}
                                      className="w-16 h-16 object-cover rounded border dark:border-gray-700"
                                      onError={(e) => {
                                        console.log('Image failed to load:', { fileName, file, mimeType });
                                        (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0yMCAyMEg0NFY0NEgyMFYyMFoiIHN0cm9rZT0iIzlCQTJCOCIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjMyIiB5PSI0MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSI4IiBmaWxsPSIjOUJBMkI4Ij5JbWFnZTwvdGV4dD4KPHN2Zz4K';
                                      }}
                                    />
                                  ) : mimeType?.startsWith('video/') ? (
                                    <div className="w-16 h-16 bg-gradient-to-br from-purple-200 to-purple-300 dark:from-purple-700 dark:to-purple-800 rounded flex items-center justify-center">
                                      <span className="text-xs font-bold text-purple-700 dark:text-purple-200">VIDEO</span>
                                    </div>
                                  ) : mimeType?.startsWith('audio/') ? (
                                    <div className="w-16 h-16 bg-gradient-to-br from-green-200 to-green-300 dark:from-green-700 dark:to-green-800 rounded flex items-center justify-center">
                                      <span className="text-xs font-bold text-green-700 dark:text-green-200">AUDIO</span>
                                    </div>
                                  ) : (
                                    <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center relative">
                                      <FileImage className="h-6 w-6 text-gray-400" />
                                      <span className="text-xs absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white px-1 rounded-b text-center truncate">
                                        {(originalName || fileName)?.split('.').pop()?.toUpperCase() || 'FILE'}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(content.createdAt).toLocaleDateString('fr-FR')}
                        </div>
                        <Button
                          size="sm" 
                          variant="outline"
                          onClick={() => setSelectedContent(content)}
                          className="h-7 px-2"
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Draft/Processing Content Section */}
          {contents.filter((c: ContentSubmission) => c.status !== 'published').length > 0 && (
            <div>
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Badge variant="secondary">
                  {contents.filter((c: ContentSubmission) => c.status !== 'published').length}
                </Badge>
                Contenu en Attente
              </h2>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {contents.filter((c: ContentSubmission) => c.status !== 'published').map((content: ContentSubmission) => (
                  <Card key={content.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg line-clamp-2 mb-2">
                            {content.generatedTitle || "Titre généré par l'IA"}
                          </CardTitle>
                          {getStatusBadge(content.status)}
                        </div>
                        <div className="flex gap-1">
                          {content.mediaFiles?.length > 0 && (
                            <FileImage className="h-4 w-4 text-gray-500" />
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent className="pb-3">
                      <p className="text-sm text-gray-600 dark:text-gray-300 mb-3 line-clamp-3">
                        {content.generatedDescription || "Description générée par l'IA"}
                      </p>
                      
                      {/* Display uploaded images */}
                      {content.mediaFiles && content.mediaFiles.length > 0 && (
                        <div className="mb-3">
                          <div className="flex flex-wrap gap-2">
                            {content.mediaFiles.slice(0, 2).map((file: any, index: number) => {
                              // Support pour différents formats de données de fichiers  
                              const fileName = typeof file === 'string' ? file : (file.filename || file.originalname);
                              const mimeType = typeof file === 'string' ? (file.includes('.jpg') || file.includes('.jpeg') ? 'image/jpeg' : 
                                                                           file.includes('.png') ? 'image/png' :
                                                                           file.includes('.gif') ? 'image/gif' :
                                                                           file.includes('.mp4') ? 'video/mp4' :
                                                                           file.includes('.mp3') ? 'audio/mp3' : 'unknown') : file.mimetype;
                              const originalName = typeof file === 'string' ? file : file.originalname;
                              
                              return (
                                <div key={index} className="relative">
                                  {mimeType?.startsWith('image/') ? (
                                    <img 
                                      src={`/api/media/${fileName}`}
                                      alt={`Média ${index + 1}`}
                                      className="w-16 h-16 object-cover rounded border dark:border-gray-700"
                                      onError={(e) => {
                                        console.log('Image failed to load (draft):', { fileName, file, mimeType });
                                        (e.target as HTMLImageElement).src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjRjNGNEY2Ii8+CjxwYXRoIGQ9Ik0yMCAyMEg0NFY0NEgyMFYyMFoiIHN0cm9rZT0iIzlCQTJCOCIgc3Ryb2tlLXdpZHRoPSIyIi8+Cjx0ZXh0IHg9IjMyIiB5PSI0MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSI4IiBmaWxsPSIjOUJBMkI4Ij5JbWFnZTwvdGV4dD4KPHN2Zz4K';
                                      }}
                                    />
                                  ) : mimeType?.startsWith('video/') ? (
                                    <div className="w-16 h-16 bg-gradient-to-br from-red-200 to-red-300 dark:from-red-700 dark:to-red-800 rounded flex items-center justify-center">
                                      <span className="text-xs font-bold text-red-700 dark:text-red-200">VIDEO</span>
                                    </div>
                                  ) : mimeType?.startsWith('audio/') ? (
                                    <div className="w-16 h-16 bg-gradient-to-br from-yellow-200 to-yellow-300 dark:from-yellow-700 dark:to-yellow-800 rounded flex items-center justify-center">
                                      <span className="text-xs font-bold text-yellow-700 dark:text-yellow-200">AUDIO</span>
                                    </div>
                                  ) : (
                                    <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center relative">
                                      <FileImage className="h-6 w-6 text-gray-400" />
                                      <span className="text-xs absolute bottom-0 left-0 right-0 bg-black bg-opacity-70 text-white px-1 rounded-b text-center truncate">
                                        {(originalName || fileName)?.split('.').pop()?.toUpperCase() || 'FILE'}
                                      </span>
                                    </div>
                                  )}
                                  {content.mediaFiles.length > 2 && index === 1 && (
                                    <div className="absolute inset-0 bg-black bg-opacity-50 rounded flex items-center justify-center text-white text-xs">
                                      +{content.mediaFiles.length - 2}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(content.createdAt).toLocaleDateString('fr-FR')}
                        </div>
                        <div className="flex gap-1">
                          <Button
                            size="sm" 
                            variant="outline"
                            onClick={() => setSelectedContent(content)}
                            className="h-7 px-2"
                          >
                            <Eye className="h-3 w-3" />
                          </Button>
                          {content.status === 'draft' && availablePlatforms.length > 0 && (
                            <Button
                              size="sm"
                              variant="default" 
                              onClick={() => {
                                setSelectedContent(content);
                                setPublishPlatforms(availablePlatforms);
                              }}
                              className="h-7 px-2"
                            >
                              <Share className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>

        {contents.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500 dark:text-gray-400">
              <FileImage className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium mb-2">Aucun contenu créé</p>
              <p>Créez du contenu avec l'IA dans l'onglet BYOP pour le voir apparaître ici.</p>
            </div>
          </div>
        )}

        {/* Publishing Modal */}
        {selectedContent && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <CardHeader>
                <CardTitle>Publier le Contenu</CardTitle>
                <CardDescription>
                  Sélectionnez les plateformes où publier ce contenu
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <h3 className="font-medium mb-2 dark:text-gray-200">Titre:</h3>
                  <p className="text-sm bg-gray-50 dark:bg-gray-800 dark:text-gray-200 p-2 rounded">
                    {selectedContent.generatedTitle}
                  </p>
                </div>
                
                <div>
                  <h3 className="font-medium mb-2 dark:text-gray-200">Description:</h3>
                  <p className="text-sm bg-gray-50 dark:bg-gray-800 dark:text-gray-200 p-2 rounded">
                    {selectedContent.generatedDescription}
                  </p>
                </div>

                {selectedContent.generatedHashtags && (
                  <div>
                    <h3 className="font-medium mb-2 dark:text-gray-200">Hashtags:</h3>
                    <p className="text-sm text-blue-600 dark:text-blue-400 bg-gray-50 dark:bg-gray-800 p-2 rounded">
                      {selectedContent.generatedHashtags}
                    </p>
                  </div>
                )}

                {availablePlatforms.length > 0 ? (
                  <div>
                    <h3 className="font-medium mb-2 dark:text-gray-200">Plateformes disponibles:</h3>
                    <div className="space-y-2">
                      {availablePlatforms.map((platform: string) => (
                        <label key={platform} className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={publishPlatforms.includes(platform)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setPublishPlatforms([...publishPlatforms, platform]);
                              } else {
                                setPublishPlatforms(publishPlatforms.filter(p => p !== platform));
                              }
                            }}
                            className="rounded"
                          />
                          <span className="capitalize dark:text-gray-200">{platform}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500 dark:text-gray-400">
                    <p>Aucune plateforme connectée.</p>
                    <p className="text-sm">Connectez vos réseaux sociaux pour publier du contenu.</p>
                  </div>
                )}

                <div className="flex gap-2 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSelectedContent(null);
                      setPublishPlatforms([]);
                    }}
                    className="flex-1"
                  >
                    Annuler
                  </Button>
                  {availablePlatforms.length > 0 && (
                    <Button
                      onClick={handlePublish}
                      disabled={publishPlatforms.length === 0 || publishMutation.isPending}
                      className="flex-1"
                    >
                      {publishMutation.isPending ? "Publication..." : "Publier"}
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}