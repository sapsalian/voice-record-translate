import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { fetchConfig, updateConfig } from '@/api/client';
import { LANGUAGES } from '@/types/config';
import type { Config } from '@/types/config';

interface Props {
  onBack: () => void;
}

export function SettingsPage({ onBack }: Props) {
  const [config, setConfig] = useState<Config>({
    openai_api_key: '',
    soniox_api_key: '',
    target_lang: 'ko',
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchConfig()
      .then(setConfig)
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    await updateConfig(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b px-4 h-14 flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          ← 뒤로
        </Button>
        <h1 className="font-semibold text-lg">설정</h1>
      </header>

      <main className="px-4 py-6 max-w-md mx-auto space-y-6">
        <div className="space-y-2">
          <Label htmlFor="openai-key">OpenAI API Key (번역용)</Label>
          <Input
            id="openai-key"
            type="password"
            placeholder="sk-..."
            value={config.openai_api_key}
            onChange={(e) => setConfig((c) => ({ ...c, openai_api_key: e.target.value }))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="soniox-key">Soniox API Key (전사용)</Label>
          <Input
            id="soniox-key"
            type="password"
            placeholder="soniox-..."
            value={config.soniox_api_key}
            onChange={(e) => setConfig((c) => ({ ...c, soniox_api_key: e.target.value }))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="target-lang">번역 언어</Label>
          <select
            id="target-lang"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={config.target_lang}
            onChange={(e) => setConfig((c) => ({ ...c, target_lang: e.target.value }))}
          >
            {Object.entries(LANGUAGES).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <Button onClick={handleSave} className="w-full">
          {saved ? '저장됨 ✓' : '저장'}
        </Button>
      </main>
    </div>
  );
}
