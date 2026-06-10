import { Download, QrCode, Trash2, Award, TrendingUp } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import './HowItWorks.css';

const HowItWorks = () => {
    const { t } = useLanguage();

    const steps = [
        {
            icon: Download,
            number: '01',
            titleKey: 'step1Title',
            descKey: 'step1Desc'
        },
        {
            icon: QrCode,
            number: '02',
            titleKey: 'step2Title',
            descKey: 'step2Desc'
        },
        {
            icon: Trash2,
            number: '03',
            titleKey: 'step3Title',
            descKey: 'step3Desc'
        },
        {
            icon: Award,
            number: '04',
            titleKey: 'step4Title',
            descKey: 'step4Desc'
        },
        {
            icon: TrendingUp,
            number: '05',
            titleKey: 'step5Title',
            descKey: 'step5Desc'
        }
    ];

    return (
        <section className="section how-it-works">
            <div className="container">
                <div className="section-header">
                    <h2 className="heading-2">
                        {t('howItWorksTitle')} <span className="text-gradient">{t('howItWorksTitle2')}</span>
                    </h2>
                    <p className="section-description">
                        {t('howItWorksDescription')}
                    </p>
                </div>

                <div className="steps-container">
                    {steps.map((step, index) => {
                        const Icon = step.icon;
                        return (
                            <div key={index} className="step-card glass">
                                <div className="step-number">{step.number}</div>
                                <div className="step-icon">
                                    <Icon size={40} />
                                </div>
                                <h3 className="step-title">{t(step.titleKey)}</h3>
                                <p className="step-description">{t(step.descKey)}</p>
                                {index < steps.length - 1 && (
                                    <div className="step-connector"></div>
                                )}
                            </div>
                        );
                    })}
                </div>

                <div className="steps-visual">
                    <div className="flow-line"></div>
                </div>
            </div>
        </section>
    );
};

export default HowItWorks;
