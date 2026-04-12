/**
 * Terraform configuration tab for AWS provider
 */
import { useState } from 'react';
import { Download, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface TerraformTabProps {
  accountId: string;
  onAccountIdChange: (id: string) => void;
  terraformCode: string | null;
  onGenerateTerraform: () => void;
  isGenerating: boolean;
  roleArn: string;
  onRoleArnChange: (arn: string) => void;
  region: string;
  onRegionChange: (region: string) => void;
  regions: string[];
  onValidate: () => void;
  isValidating: boolean;
}

export function TerraformTab({
  accountId,
  onAccountIdChange,
  terraformCode,
  onGenerateTerraform,
  isGenerating,
  roleArn,
  onRoleArnChange,
  region,
  onRegionChange,
  regions,
  onValidate,
  isValidating,
}: TerraformTabProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (terraformCode) {
      navigator.clipboard.writeText(terraformCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (terraformCode) {
      const blob = new Blob([terraformCode], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'sre-agent-aws-role.tf';
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="account-id">Step 1: Enter your AWS Account ID</Label>
        <Input
          id="account-id"
          placeholder="123456789012"
          value={accountId}
          onChange={(e) => onAccountIdChange(e.target.value)}
        />
      </div>

      {accountId && (
        <Button onClick={onGenerateTerraform} disabled={isGenerating}>
          Generate Terraform Code
        </Button>
      )}

      {terraformCode && (
        <>
          <div className="space-y-2">
            <Label>Step 2: Copy and run this Terraform in your account</Label>
            <div className="relative">
              <pre className="max-h-96 overflow-auto rounded-lg border bg-muted p-4 text-xs">
                <code>{terraformCode}</code>
              </pre>
              <div className="absolute right-2 top-2 flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleCopy}
                  aria-label="Copy Terraform code"
                >
                  {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleDownload}
                  aria-label="Download Terraform file"
                >
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="role-arn">Step 3: Enter the Role ARN after deployment</Label>
            <Input
              id="role-arn"
              placeholder="arn:aws:iam::123456789012:role/SREAgentRole"
              value={roleArn}
              onChange={(e) => onRoleArnChange(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="region">Step 4: Select primary region</Label>
            <select
              id="region"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={region}
              onChange={(e) => onRegionChange(e.target.value)}
            >
              {regions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <Button onClick={onValidate} disabled={!roleArn || isValidating}>
            Validate Connection
          </Button>
        </>
      )}
    </div>
  );
}
