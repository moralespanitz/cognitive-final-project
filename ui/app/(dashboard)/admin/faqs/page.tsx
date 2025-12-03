'use client';

import { useEffect, useState } from 'react';
import { faqsApi } from '@/lib/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';

interface FAQ {
  id: number;
  question: string;
  answer: string;
  category: string;
  keywords: string;
  priority: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const categories = [
  { value: 'GENERAL', label: 'General', icon: '📖' },
  { value: 'VEHICLES', label: 'Vehicles', icon: '🚕' },
  { value: 'DRIVERS', label: 'Drivers', icon: '👤' },
  { value: 'TRIPS', label: 'Trips', icon: '🛣️' },
  { value: 'INCIDENTS', label: 'Incidents', icon: '⚠️' },
  { value: 'SYSTEM', label: 'System', icon: '⚙️' },
];

export default function FAQsPage() {
  const [faqs, setFaqs] = useState<FAQ[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedFaq, setSelectedFaq] = useState<FAQ | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('ALL');

  const [formData, setFormData] = useState({
    question: '',
    answer: '',
    category: 'GENERAL',
    keywords: '',
    priority: 5,
    is_active: true,
  });

  useEffect(() => {
    loadFaqs();
  }, []);

  const loadFaqs = async () => {
    try {
      const data = await faqsApi.getAll();
      setFaqs(data);
    } catch (error) {
      console.error('Failed to load FAQs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await faqsApi.create(formData);
      setIsCreateOpen(false);
      resetForm();
      await loadFaqs();
    } catch (error) {
      console.error('Failed to create FAQ:', error);
      alert('Failed to create FAQ');
    }
  };

  const handleUpdate = async () => {
    if (!selectedFaq) return;

    try {
      await faqsApi.update(selectedFaq.id, formData);
      setIsEditOpen(false);
      setSelectedFaq(null);
      resetForm();
      await loadFaqs();
    } catch (error) {
      console.error('Failed to update FAQ:', error);
      alert('Failed to update FAQ');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this FAQ?')) return;

    try {
      await faqsApi.delete(id);
      await loadFaqs();
    } catch (error) {
      console.error('Failed to delete FAQ:', error);
      alert('Failed to delete FAQ');
    }
  };

  const handleToggleActive = async (faq: FAQ) => {
    try {
      await faqsApi.update(faq.id, { is_active: !faq.is_active });
      await loadFaqs();
    } catch (error) {
      console.error('Failed to toggle FAQ:', error);
      alert('Failed to toggle FAQ');
    }
  };

  const openEditDialog = (faq: FAQ) => {
    setSelectedFaq(faq);
    setFormData({
      question: faq.question,
      answer: faq.answer,
      category: faq.category,
      keywords: faq.keywords || '',
      priority: faq.priority,
      is_active: faq.is_active,
    });
    setIsEditOpen(true);
  };

  const resetForm = () => {
    setFormData({
      question: '',
      answer: '',
      category: 'GENERAL',
      keywords: '',
      priority: 5,
      is_active: true,
    });
  };

  const getCategoryInfo = (category: string) => {
    return categories.find((c) => c.value === category) || categories[0];
  };

  const filteredFaqs = faqs.filter((faq) => {
    const matchesSearch =
      faq.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (faq.keywords && faq.keywords.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesCategory = filterCategory === 'ALL' || faq.category === filterCategory;

    return matchesSearch && matchesCategory;
  });

  const sortedFaqs = [...filteredFaqs].sort((a, b) => b.priority - a.priority);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading FAQs...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">FAQ Management</h1>
          <p className="text-muted-foreground">
            Manage frequently asked questions for AI chatbot
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>Add FAQ</Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Input
            placeholder="Search questions, answers, or keywords..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <Select value={filterCategory} onValueChange={setFilterCategory}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Categories</SelectItem>
            {categories.map((cat) => (
              <SelectItem key={cat.value} value={cat.value}>
                {cat.icon} {cat.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* FAQs List */}
      <div className="space-y-4">
        {sortedFaqs.map((faq) => {
          const categoryInfo = getCategoryInfo(faq.category);
          return (
            <div
              key={faq.id}
              className="border rounded-lg p-4 space-y-3 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start gap-4">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{categoryInfo.icon}</span>
                    <Badge variant="outline">{categoryInfo.label}</Badge>
                    <Badge variant="secondary">Priority: {faq.priority}</Badge>
                    <Badge className={faq.is_active ? 'bg-green-500' : 'bg-gray-500'}>
                      {faq.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <h3 className="font-semibold text-lg">{faq.question}</h3>
                  <p className="text-muted-foreground">{faq.answer}</p>
                  {faq.keywords && (
                    <div className="flex gap-1 flex-wrap">
                      {faq.keywords.split(',').map((keyword, idx) => (
                        <span
                          key={idx}
                          className="text-xs bg-secondary px-2 py-1 rounded"
                        >
                          {keyword.trim()}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex flex-col gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleToggleActive(faq)}
                  >
                    {faq.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openEditDialog(faq)}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(faq.id)}
                  >
                    Delete
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {sortedFaqs.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No FAQs found</p>
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add New FAQ</DialogTitle>
            <DialogDescription>
              Create a new frequently asked question
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Question *</Label>
              <Input
                value={formData.question}
                onChange={(e) =>
                  setFormData({ ...formData, question: e.target.value })
                }
                placeholder="How do I track my fleet in real-time?"
              />
            </div>
            <div>
              <Label>Answer *</Label>
              <Textarea
                value={formData.answer}
                onChange={(e) =>
                  setFormData({ ...formData, answer: e.target.value })
                }
                placeholder="Navigate to the Dashboard or Live Map..."
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) =>
                    setFormData({ ...formData, category: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.icon} {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Priority (0-10)</Label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  value={formData.priority}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      priority: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>
            <div>
              <Label>Keywords (comma-separated)</Label>
              <Input
                value={formData.keywords}
                onChange={(e) =>
                  setFormData({ ...formData, keywords: e.target.value })
                }
                placeholder="track, real-time, map, location"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_active: checked })
                }
              />
              <Label>Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsCreateOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreate}>Create FAQ</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit FAQ</DialogTitle>
            <DialogDescription>Update FAQ information</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Question *</Label>
              <Input
                value={formData.question}
                onChange={(e) =>
                  setFormData({ ...formData, question: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Answer *</Label>
              <Textarea
                value={formData.answer}
                onChange={(e) =>
                  setFormData({ ...formData, answer: e.target.value })
                }
                rows={4}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Category</Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) =>
                    setFormData({ ...formData, category: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.icon} {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Priority (0-10)</Label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  value={formData.priority}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      priority: parseInt(e.target.value) || 0,
                    })
                  }
                />
              </div>
            </div>
            <div>
              <Label>Keywords (comma-separated)</Label>
              <Input
                value={formData.keywords}
                onChange={(e) =>
                  setFormData({ ...formData, keywords: e.target.value })
                }
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_active: checked })
                }
              />
              <Label>Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsEditOpen(false);
                resetForm();
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleUpdate}>Update FAQ</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
