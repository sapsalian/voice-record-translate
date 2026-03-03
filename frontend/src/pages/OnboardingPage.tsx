import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { validateKeys, updateConfig } from '@/api/client';
import { UI_LANGUAGES } from '@/types/config';
import { getT } from '@/i18n';

interface Props {
  initialLang: string;
  onComplete: (lang: string) => void;
}

export function OnboardingPage({ initialLang, onComplete }: Props) {
  const [lang, setLang] = useState(initialLang);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [openaiKey, setOpenaiKey] = useState('');
  const [sonioxKey, setSonioxKey] = useState('');
  const [validating, setValidating] = useState(false);
  const [openaiError, setOpenaiError] = useState(false);
  const [sonioxError, setSonioxError] = useState(false);

  const t = getT(lang);

  const handleLangNext = () => {
    setStep(2);
  };

  const handleKeysNext = async () => {
    setOpenaiError(false);
    setSonioxError(false);
    setValidating(true);
    try {
      const result = await validateKeys(openaiKey, sonioxKey);
      if (result.openai && result.soniox) {
        setStep(3);
      } else {
        setOpenaiError(!result.openai);
        setSonioxError(!result.soniox);
      }
    } catch {
      setOpenaiError(true);
      setSonioxError(true);
    } finally {
      setValidating(false);
    }
  };

  const handleStart = async () => {
    await updateConfig({ openai_api_key: openaiKey, soniox_api_key: sonioxKey, ui_lang: lang });
    localStorage.setItem('mainWalkthroughNeeded', '1');
    localStorage.setItem('viewerWalkthroughNeeded', '1');
    onComplete(lang);
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Step indicators */}
        <div className="flex gap-2 justify-center mb-2">
          {([1, 2, 3] as const).map((s) => (
            <div
              key={s}
              className={`h-1.5 w-8 rounded-full transition-colors ${s <= step ? 'bg-primary' : 'bg-muted'}`}
            />
          ))}
        </div>

        {step === 1 && (
          <>
            <h1 className="text-xl font-semibold text-center">{t('onboarding_lang_title')}</h1>
            <select
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={lang}
              onChange={(e) => setLang(e.target.value)}
            >
              {Object.entries(UI_LANGUAGES).map(([code, name]) => (
                <option key={code} value={code}>{name}</option>
              ))}
            </select>
            <Button className="w-full" onClick={handleLangNext}>
              {t('onboarding_next')}
            </Button>
          </>
        )}

        {step === 2 && (
          <>
            <h1 className="text-xl font-semibold text-center">{t('onboarding_keys_title')}</h1>

            <div className="space-y-1">
              <Label htmlFor="ob-openai">OpenAI API Key</Label>
              <Input
                id="ob-openai"
                type="password"
                placeholder="sk-..."
                value={openaiKey}
                onChange={(e) => { setOpenaiKey(e.target.value); setOpenaiError(false); }}
              />
              {openaiError && (
                <p className="text-xs text-destructive">{t('onboarding_openai_invalid')}</p>
              )}
              <button
                className="text-xs text-primary underline underline-offset-2"
                onClick={() => window.open('https://platform.openai.com/api-keys')}
                type="button"
              >
                {t('onboarding_openai_link')}
              </button>
            </div>

            <div className="space-y-1">
              <Label htmlFor="ob-soniox">Soniox API Key</Label>
              <Input
                id="ob-soniox"
                type="password"
                placeholder="soniox-..."
                value={sonioxKey}
                onChange={(e) => { setSonioxKey(e.target.value); setSonioxError(false); }}
              />
              {sonioxError && (
                <p className="text-xs text-destructive">{t('onboarding_soniox_invalid')}</p>
              )}
              <button
                className="text-xs text-primary underline underline-offset-2"
                onClick={() => window.open('https://console.soniox.com/api-keys')}
                type="button"
              >
                {t('onboarding_soniox_link')}
              </button>
            </div>

            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setStep(1)}>
                {t('onboarding_back')}
              </Button>
              <Button
                className="flex-1"
                onClick={handleKeysNext}
                disabled={validating || !openaiKey || !sonioxKey}
              >
                {validating ? t('onboarding_validating') : t('onboarding_next')}
              </Button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h1 className="text-xl font-semibold text-center">{t('onboarding_usage_title')}</h1>
            <ul className="space-y-3 text-sm text-muted-foreground">
              <li className="flex gap-2"><span>📁</span><span>{t('onboarding_usage_add')}</span></li>
              <li className="flex gap-2"><span>⏳</span><span>{t('onboarding_usage_wait')}</span></li>
              <li className="flex gap-2"><span>📝</span><span>{t('onboarding_usage_review')}</span></li>
            </ul>
            <div className="flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => setStep(2)}>
                {t('onboarding_back')}
              </Button>
              <Button className="flex-1" onClick={handleStart}>
                {t('onboarding_start')}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
