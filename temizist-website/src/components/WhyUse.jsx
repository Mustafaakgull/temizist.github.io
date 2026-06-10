import { Coins, Leaf, MapPin, BarChart3 } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import './WhyUse.css';

const WhyUse = () => {
  const { t } = useLanguage();

  const benefits = [
    {
      icon: Coins,
      titleKey: 'earnMoney',
      descKey: 'earnMoneyDesc',
      color: '#FFB800'
    },
    {
      icon: Leaf,
      titleKey: 'protectEnvironment',
      descKey: 'protectEnvironmentDesc',
      color: '#00D665'
    },
    {
      icon: MapPin,
      titleKey: 'findNearby',
      descKey: 'findNearbyDesc',
      color: '#3B82F6'
    },
    {
      icon: BarChart3,
      titleKey: 'trackProgress',
      descKey: 'trackProgressDesc',
      color: '#10B981'
    }
  ];

  return (
    <section className="section why-use">
      <div className="container">
        <div className="section-header">
          <h2 className="heading-2">
            {t('whyUseTitle')} <span className="text-gradient">TemizIST?</span>
          </h2>
          <p className="section-description">
            {t('whyUseDescription')}
          </p>
        </div>

        <div className="benefits-grid">
          {benefits.map((benefit, index) => {
            const Icon = benefit.icon;
            return (
              <div key={index} className="benefit-card glass">
                <div
                  className="benefit-icon"
                  style={{ '--icon-color': benefit.color }}
                >
                  <Icon size={48} />
                </div>
                <h3 className="benefit-title">{t(benefit.titleKey)}</h3>
                <p className="benefit-description">{t(benefit.descKey)}</p>
                <div className="benefit-decoration"></div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default WhyUse;
