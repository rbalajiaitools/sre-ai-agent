/**
 * Knowledge Graph Page - Main page for managing knowledge base
 */
import { useState } from 'react';
import { 
  Search, 
  Plus, 
  FileText, 
  Code, 
  GitBranch, 
  Link as LinkIcon,
  BookOpen,
  User,
  Calendar,
  Tag
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useKnowledgeList } from '../hooks';
import { Knowledge } from '../api';
import { CreateKnowledgeDialog } from './CreateKnowledgeDialog';
import { KnowledgeDetailDialog } from './KnowledgeDetailDialog';
import { format } from 'date-fns';

const typeIcons = {
  runbook: BookOpen,
  architecture: GitBranch,
  code_snippet: Code,
  investigation: FileText,
  external_link: LinkIcon,
};

const typeLabels = {
  runbook: 'Runbook',
  architecture: 'Architecture',
  code_snippet: 'Code Snippet',
  investigation: 'Investigation',
  external_link: 'External Link',
};

export function KnowledgeGraphPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [selectedKnowledge, setSelectedKnowledge] = useState<Knowledge | null>(null);

  const { data: allKnowledge, isLoading } = useKnowledgeList(typeFilter || undefined);

  // Filter by search query
  const filteredKnowledge = allKnowledge?.filter((k) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      k.title.toLowerCase().includes(query) ||
      k.description?.toLowerCase().includes(query) ||
      k.tags?.some(tag => tag.toLowerCase().includes(query))
    );
  }) || [];

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="bg-white border-b px-6 py-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Knowledge Graph</h1>
            <p className="text-sm text-gray-500 mt-1">
              Runbooks, postmortems, and architectural docs that SRE.ai can reference.
            </p>
          </div>
          <Button
            onClick={() => setCreateDialogOpen(true)}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Add Document
          </Button>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search knowledge base..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
          >
            <option value="">All Types</option>
            <option value="runbook">Runbooks</option>
            <option value="architecture">Architecture</option>
            <option value="code_snippet">Code Snippets</option>
            <option value="investigation">Investigations</option>
            <option value="external_link">External Links</option>
          </select>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-sm text-gray-500">Loading knowledge...</div>
          </div>
        ) : filteredKnowledge.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <FileText className="h-16 w-16 text-gray-400 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {searchQuery || typeFilter ? 'No knowledge found' : 'No knowledge yet'}
            </h2>
            <p className="text-sm text-gray-500 max-w-md mb-4">
              {searchQuery || typeFilter
                ? 'Try adjusting your search or filters'
                : 'Start building your knowledge base by adding runbooks, architecture docs, or code snippets.'}
            </p>
            {!searchQuery && !typeFilter && (
              <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
                <Plus className="h-4 w-4" />
                Add Your First Document
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredKnowledge.map((knowledge) => {
              const Icon = typeIcons[knowledge.type];
              return (
                <button
                  key={knowledge.id}
                  onClick={() => setSelectedKnowledge(knowledge)}
                  className="bg-white rounded-lg border border-gray-200 p-4 hover:border-teal-500 hover:shadow-sm transition-all text-left"
                >
                  {/* Header */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className="p-2 bg-gray-100 rounded">
                      <Icon className="h-5 w-5 text-gray-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900 mb-1 line-clamp-1">
                        {knowledge.title}
                      </h3>
                      {knowledge.description && (
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {knowledge.description}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Tags */}
                  {knowledge.tags && knowledge.tags.length > 0 && (
                    <div className="flex items-center gap-2 mb-3 flex-wrap">
                      <Tag className="h-3 w-3 text-gray-400" />
                      {knowledge.tags.slice(0, 4).map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs"
                        >
                          {tag}
                        </span>
                      ))}
                      {knowledge.tags.length > 4 && (
                        <span className="text-xs text-gray-500">
                          +{knowledge.tags.length - 4} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Footer */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      <span>{knowledge.created_by || 'Unknown'}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      <span>{format(new Date(knowledge.created_at), 'M/d/yyyy')}</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Dialogs */}
      <CreateKnowledgeDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
      />

      {selectedKnowledge && (
        <KnowledgeDetailDialog
          knowledge={selectedKnowledge}
          open={!!selectedKnowledge}
          onClose={() => setSelectedKnowledge(null)}
        />
      )}
    </div>
  );
}
