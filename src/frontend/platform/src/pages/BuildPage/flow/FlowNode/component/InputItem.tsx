import { Input } from "@/components/bs-ui/input";
import { Label } from "@/components/bs-ui/label";
import { QuestionTooltip } from "@/components/bs-ui/tooltip";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

export default function InputItem({ type = 'text', char = false, linefeed = false, data, onChange, i18nPrefix, label }) {
    const [value, setValue] = useState(data.value ? String(data.value) : '');
    const { t } = useTranslation('flow');

    // 初始化时同步外部数据（数字类型确保为整数）
    useEffect(() => {
        if (data.value !== undefined) {
            if (type === 'number') {
                const intValue = parseInt(data.value, 10);
                setValue(isNaN(intValue) ? '' : String(intValue));
            } else {
                setValue(String(data.value));
            }
        }
    }, [data.value, type]);

    // 处理输入变化
    const handleChange = (inputValue) => {
        if (type === 'number') {
            // 数字类型：过滤掉小数点和非数字字符
            const filteredValue = inputValue.replace(/[^\d]/g, '');
            const intValue = filteredValue ? parseInt(filteredValue, 10) : '';
            setValue(filteredValue);
            onChange(intValue);
        } else {
            // 文本类型：直接使用输入值
            setValue(inputValue);
            onChange(inputValue);
        }
    };

    if (char) return (
        <div
            className={`node-item mb-4 ${!linefeed ? 'flex items-center justify-between' : ''}`}
            data-key={data.key}
        >
            <Label className="flex items-center bisheng-label">
                {label || data.label && t(`${i18nPrefix}label`)}
                {data.help && <QuestionTooltip content={t(`${i18nPrefix}help`)} />}
            </Label>
            <div className={`nodrag ${char ? 'w-32 flex items-center gap-3' : ''} ${linefeed ? 'mt-2' : ''}`}>
                <Input
                    className="min-w-24"
                    value={value}
                    type={type}
                    min={data.min}
                    max={data.max}
                    onChange={(e) => handleChange(e.target.value)}
                />
                <Label className="bisheng-label">{t('character')}</Label>
            </div>
        </div>
    );

    return (
        <div className='node-item mb-4' data-key={data.key}>
            <Label className="flex items-center bisheng-label">
                {data.label && t(`${i18nPrefix}label`)}
                {data.help && <QuestionTooltip content={t(`${i18nPrefix}help`)} />}
            </Label>
            <Input
                className="mt-2 nodrag"
                value={value}
                type={type}
                min={data.min}
                max={data.max}
                onChange={(e) => handleChange(e.target.value)}
            />
        </div>
    );
};