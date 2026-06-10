import { Recycle, Download, Smartphone } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import './Hero.css';

const Hero = () => {
    const { t } = useLanguage();

    const scrollToSection = (sectionId) => {
        const element = document.getElementById(sectionId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    };

    return (
        <section className="hero">
            <div className="container">
                <div className="hero-content">
                    <div className="hero-text animate-fade-in-up">
                        <div className="hero-badge">
                            <Recycle size={20} />
                            <span>{t('tagline')}</span>
                        </div>

                        <h1 className="heading-1 hero-title">
                            {t('heroTitle')}
                            <span className="text-gradient"> {t('heroTitleGradient')}</span>
                        </h1>

                        <p className="hero-description">
                            {t('heroDescription')}
                        </p>

                        <div className="hero-cta">
                            <button className="btn btn-primary btn-lg">
                                <Download size={20} />
                                {t('downloadNow')}
                            </button>
                            <button className="btn btn-outline btn-lg" onClick={() => scrollToSection('how-it-works')}>
                                <Smartphone size={20} />
                                {t('howItWorksBtn')}
                            </button>
                        </div>

                        <div className="hero-stats">
                            <div className="stat">
                                <div className="stat-value text-gradient">10K+</div>
                                <div className="stat-label">{t('activeUsers')}</div>
                            </div>
                            <div className="stat">
                                <div className="stat-value text-gradient">50K+</div>
                                <div className="stat-label">{t('recycledWaste')}</div>
                            </div>
                            <div className="stat">
                                <div className="stat-value text-gradient">2.5T</div>
                                <div className="stat-label">{t('reducedCO2')}</div>
                            </div>
                        </div>
                    </div>

                    <div className="hero-visual">
                        <div className="phone-mockup animate-float">
                            <div className="phone-frame glass">
                                <div className="phone-screen">
                                    <div className="screen-header">
                                        <Recycle size={24} color="#00D665" />
                                        <span>TEMİZİST</span>
                                    </div>
                                    <div className="screen-content">
                                        <div className="recycle-icon-large">
                                            <Recycle size={90} color="#00D665" />
                                        </div>
                                        <h2 className="screen-title">{t('tagline')}</h2>
                                        <p className="screen-subtitle">
                                            {t('heroDescription').split('.')[0]}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div className="phone-glow"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="hero-background">
                <div className="gradient-orb orb-1"></div>
                <div className="gradient-orb orb-2"></div>
                <div className="grid-pattern"></div>
            </div>
        </section>
    );
};

export default Hero;

