import { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react';
import { faqData } from '../utils/faqData';

function FAQ() {
  const [openId, setOpenId] = useState(1);

  const toggleQuestion = (id) => {
    setOpenId(openId === id ? null : id);
  };

  return (
    <div className="min-h-screen pb-24 px-4 pt-20">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 glass-card rounded-full mb-4">
            <HelpCircle className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            Часто задаваемые вопросы
          </h1>
          <p className="text-white/70">
            Найдите ответы на самые популярные вопросы о нашей продукции
          </p>
        </div>

        <div className="space-y-3">
          {faqData.map((item) => {
            const isOpen = openId === item.id;
            return (
              <div
                key={item.id}
                className="glass-card overflow-hidden transition-all duration-300"
              >
                <button
                  onClick={() => toggleQuestion(item.id)}
                  className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-white/5 transition-colors"
                  aria-expanded={isOpen}
                  aria-controls={`faq-answer-${item.id}`}
                  id={`faq-question-${item.id}`}
                >
                  <span className="text-white font-medium text-lg pr-4">
                    {item.question}
                  </span>
                  <div className="flex-shrink-0">
                    {isOpen ? (
                      <ChevronUp className="w-5 h-5 text-white" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-white" />
                    )}
                  </div>
                </button>

                <div
                  id={`faq-answer-${item.id}`}
                  className={`overflow-hidden transition-all duration-300 ${
                    isOpen ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
                  }`}
                  role="region"
                  aria-labelledby={`faq-question-${item.id}`}
                  aria-hidden={!isOpen}
                >
                  <div className="px-5 pb-4 pt-2 border-t border-white/10">
                    <p className="text-white/80 whitespace-pre-line leading-relaxed">
                      {item.answer}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-8 glass-card p-6 text-center">
          <p className="text-white/70 mb-2">
            Не нашли ответ на свой вопрос?
          </p>
          <p className="text-white font-medium">
            Напишите нам в поддержку через Telegram бот!
          </p>
        </div>
      </div>
    </div>
  );
}

export default FAQ;
