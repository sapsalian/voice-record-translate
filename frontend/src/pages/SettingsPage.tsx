import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { fetchConfig, updateConfig } from '@/api/client';
import { UI_LANGUAGES } from '@/types/config';
import type { Config } from '@/types/config';
import { useT } from '@/LocaleContext';

interface Props {
  onBack: () => void;
  onUiLangChange: (lang: string) => void;
}

export function SettingsPage({ onBack, onUiLangChange }: Props) {
  const t = useT();
  const [config, setConfig] = useState<Config>({
    openai_api_key: '',
    soniox_api_key: '',
    ui_lang: 'ko',
  });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchConfig()
      .then(setConfig)
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    await updateConfig(config);
    onUiLangChange(config.ui_lang);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b px-4 h-14 flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={onBack}>
          {t('back')}
        </Button>
        <h1 className="font-semibold text-lg">{t('settings')}</h1>
      </header>

      <main className="px-4 py-6 max-w-md mx-auto space-y-6">
        <div className="space-y-2">
          <Label htmlFor="openai-key">{t('openai_key_label')}</Label>
          <Input
            id="openai-key"
            type="password"
            placeholder="sk-..."
            value={config.openai_api_key}
            onChange={(e) => setConfig((c) => ({ ...c, openai_api_key: e.target.value }))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="soniox-key">{t('soniox_key_label')}</Label>
          <Input
            id="soniox-key"
            type="password"
            placeholder="soniox-..."
            value={config.soniox_api_key}
            onChange={(e) => setConfig((c) => ({ ...c, soniox_api_key: e.target.value }))}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="ui-lang">{t('ui_lang_label')}</Label>
          <select
            id="ui-lang"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={config.ui_lang}
            onChange={(e) => setConfig((c) => ({ ...c, ui_lang: e.target.value }))}
          >
            {Object.entries(UI_LANGUAGES).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <Button onClick={handleSave} className="w-full">
          {saved ? t('saved') : t('save')}
        </Button>
      </main>
    </div>
  );
}
