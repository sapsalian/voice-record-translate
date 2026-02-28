import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { fetchConfig } from '@/api/client';
import { LANGUAGES } from '@/types/config';
import { useT } from '@/LocaleContext';

interface Props {
  fileNames: string[];
  onClose: () => void;
  onConfirm: (targetLang: string) => Promise<void>;
}

export function AddFilesModal({ fileNames, onClose, onConfirm }: Props) {
  const t = useT();
  const [targetLang, setTargetLang] = useState('ko');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchConfig()
      .then((c) => setTargetLang(c.ui_lang))
      .catch(() => {});
  }, []);

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm(targetLang);
    } finally {
      setLoading(false);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-background border rounded-lg shadow-lg p-6 w-80 max-w-full mx-4">
        <h2 className="font-semibold text-lg mb-4">{t('file_add_title', fileNames.length)}</h2>

        <ul className="mb-4 space-y-1 max-h-40 overflow-y-auto">
          {fileNames.map((name, i) => (
            <li key={i} className="text-sm text-muted-foreground flex items-center gap-1.5">
              <span className="shrink-0">📄</span>
              <span className="truncate">{name}</span>
            </li>
          ))}
        </ul>

        <div className="mb-6 space-y-1">
          <label className="text-sm font-medium">{t('translate_lang')}</label>
          <select
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={targetLang}
            onChange={(e) => setTargetLang(e.target.value)}
          >
            {Object.entries(LANGUAGES).map(([code, name]) => (
              <option key={code} value={code}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={loading}>
            {t('cancel')}
          </Button>
          <Button onClick={handleConfirm} disabled={loading}>
            {loading ? t('starting') : t('start')}
          </Button>
        </div>
      </div>
    </div>
  );
}
