/**
 * Save Investigation as Knowledge Dialog
 */
import { useState } from 'react';
import { X, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useConvertInvestigation } from '@/features/knowledge/hooks';
import { useNavigate } from 'react-router-dom';

interface SaveAsKnowledgeDialogProps {
  investigationId: string;
  incidentNumber: string;
  open: boolean;
  onClose: () => void;
}

export function SaveAsKnowledgeDialog({
  investigationId,
  incidentNumber,
  open,
  onClose,
}: SaveAsKnowledgeDialogProps) {
  const [title, setTitle] = useState(`Investigation: ${incidentNumber}`);
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState(incidentNumber);

  const convertMutation = useConvertInvestigation();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const tagArray = tags
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    await convertMutation.mutateAsync({
      investigation_id: investigationId,
      title,
      description: description || undefined,
      tags: tagArray.length > 0 ? tagArray : undefined,
    });

    // Reset form
    setTitle(`Investigation: ${incidentNumber}`);
    setDescription('');
    setTags(incidentNumber);

    onClose();

    // Show success message and optionally navigate to knowledge graph
    if (window.confirm('Knowledge saved successfully! Would you like to view it in the Knowledge Graph?')) {
      navigate('/knowledge');
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-teal-100 rounded-lg">
              <BookOpen className="h-5 w-5 text-teal-600" />
            </div>
            <h2 className="text-xl font-semibold">Save as Knowledge</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <p className="text-sm text-gray-600">
            Save this investigation to the Knowledge Graph so it can be referenced in future investigations.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="e.g., Lambda Memory Issue Resolution"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Brief description of what this investigation covers..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="lambda, memory, performance"
            />
            <p className="text-xs text-gray-500 mt-1">
              Tags help make this knowledge easier to find in future investigations
            </p>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={convertMutation.isPending || !title}
            >
              {convertMutation.isPending ? 'Saving...' : 'Save to Knowledge Graph'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
