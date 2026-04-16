/**
 * Users Management View - Manage workspace users and permissions
 */
import { PageHeader } from '@/components/shared/PageHeader';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Plus, Search, MoreVertical, Mail, Shield } from 'lucide-react';

// Dummy data
const USERS = [
  {
    id: '1',
    name: 'John Doe',
    email: 'john.doe@company.com',
    role: 'Admin',
    status: 'Active',
    lastActive: '2 hours ago',
  },
  {
    id: '2',
    name: 'Jane Smith',
    email: 'jane.smith@company.com',
    role: 'Member',
    status: 'Active',
    lastActive: '1 day ago',
  },
  {
    id: '3',
    name: 'Bob Johnson',
    email: 'bob.johnson@company.com',
    role: 'Member',
    status: 'Invited',
    lastActive: 'Never',
  },
];

export function UsersManagementView() {
  return (
    <div className="flex h-full flex-col">
      <PageHeader
        title="Users Management"
        description="Manage team members and their access permissions."
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mx-auto max-w-5xl space-y-6">
          {/* Header Actions */}
          <div className="flex items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Search users..."
                className="pl-9"
              />
            </div>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Invite User
            </Button>
          </div>

          {/* Users List */}
          <Card>
            <div className="divide-y">
              {USERS.map((user) => (
                <div key={user.id} className="flex items-center justify-between p-4 hover:bg-gray-50">
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-semibold">
                      {user.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium text-gray-900">{user.name}</h4>
                        <Badge
                          variant={user.status === 'Active' ? 'default' : 'secondary'}
                          className={
                            user.status === 'Active'
                              ? 'bg-green-100 text-green-800 hover:bg-green-100'
                              : 'bg-gray-100 text-gray-700'
                          }
                        >
                          {user.status}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Mail className="h-3 w-3" />
                          {user.email}
                        </span>
                        <span className="flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          {user.role}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">
                      Last active: {user.lastActive}
                    </span>
                    <Button variant="ghost" size="sm">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </Card>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="p-4">
              <div className="text-2xl font-bold text-gray-900">3</div>
              <div className="text-sm text-gray-500">Total Users</div>
            </Card>
            <Card className="p-4">
              <div className="text-2xl font-bold text-gray-900">2</div>
              <div className="text-sm text-gray-500">Active Users</div>
            </Card>
            <Card className="p-4">
              <div className="text-2xl font-bold text-gray-900">1</div>
              <div className="text-sm text-gray-500">Pending Invites</div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
