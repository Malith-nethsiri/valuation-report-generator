/**
 * PhaseTabBar — browser-tab style 3-phase navigator for MultiStepForm.
 *
 * Renders three clickable phase tabs (Documents / Inspection / Valuation)
 * and a sub-row of step dots for whichever phase is currently active.
 * Clicking a tab is always allowed (no validation gate).
 */

import React from 'react';
import { Check } from 'lucide-react';
import { Phase, FormStep, getPhaseForStepId } from '../../constants/multiStepFormConstants';

interface PhaseTabBarProps {
  phases: Phase[];
  /** Filtered & display-indexed step list from MultiStepForm. */
  activeSteps: FormStep[];
  /** 1-indexed current step position within activeSteps. */
  currentStep: number;
  onPhaseClick: (phaseId: number) => void;
  /** 1-indexed step position — matches handleStepClick signature in MultiStepForm. */
  onStepClick: (stepIndex: number) => void;
}

const PhaseTabBar: React.FC<PhaseTabBarProps> = ({
  phases,
  activeSteps,
  currentStep,
  onPhaseClick,
  onStepClick,
}) => {
  const currentStepData = activeSteps[currentStep - 1];
  const activePhaseId = currentStepData
    ? getPhaseForStepId(currentStepData.id)?.id ?? phases[0].id
    : phases[0].id;

  /** Steps within a given phase that exist in activeSteps (some may be filtered for multi-property). */
  const getPhaseSteps = (phase: Phase): Array<{ step: FormStep; globalIndex: number }> => {
    const result: Array<{ step: FormStep; globalIndex: number }> = [];
    activeSteps.forEach((step, idx) => {
      if (phase.stepIds.includes(step.id)) {
        result.push({ step, globalIndex: idx + 1 }); // 1-indexed
      }
    });
    return result;
  };

  /** Count how many steps in the phase have been visited (index <= currentStep). */
  const getVisitedCount = (phase: Phase): number =>
    getPhaseSteps(phase).filter(({ globalIndex }) => globalIndex < currentStep).length;

  return (
    <div className="mb-4 md:mb-6 md:sticky md:top-0 md:z-20 md:bg-white/95 md:backdrop-blur-sm md:py-3 md:rounded-2xl md:shadow-sm">
      {/* Phase tab row */}
      <div className="flex gap-1.5 md:gap-3 mb-4 md:mb-5">
        {phases.map((phase) => {
          const isActive = phase.id === activePhaseId;
          const phaseSteps = getPhaseSteps(phase);
          const visited = getVisitedCount(phase);
          const total = phaseSteps.length;
          const allDone = total > 0 && visited >= total;
          const PhaseIcon = phase.icon;

          return (
            <button
              key={phase.id}
              type="button"
              onClick={() => onPhaseClick(phase.id)}
              className={`
                flex-1 flex flex-col items-center gap-1 px-2 py-2 md:px-4 md:py-3 rounded-xl md:rounded-2xl border-2 transition-all duration-200
                ${isActive
                  ? `bg-gradient-to-br ${phase.color} border-transparent text-white shadow-lg scale-[1.02]`
                  : 'bg-white border-gray-200 text-gray-500 hover:border-gray-300 hover:shadow-sm'
                }
              `}
            >
              <div className="flex items-center gap-1 md:gap-2">
                {allDone && !isActive ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <PhaseIcon className={`h-4 w-4 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                )}
                <span className={`hidden md:inline text-xs md:text-sm font-semibold ${isActive ? 'text-white' : 'text-gray-600'}`}>
                  {phase.name}
                </span>
              </div>
              <span className={`hidden md:block text-xs ${isActive ? 'text-white/80' : 'text-gray-400'}`}>
                {total > 0 ? `${visited} / ${total} steps` : 'N/A'}
              </span>
            </button>
          );
        })}
      </div>

      {/* Step dots — only for the active phase */}
      {phases
        .filter((p) => p.id === activePhaseId)
        .map((phase) => {
          const phaseSteps = getPhaseSteps(phase);
          if (phaseSteps.length === 0) return null;

          return (
            <div key={phase.id} className="relative flex justify-center items-center gap-2 md:gap-3 overflow-x-auto pb-1">
              {/* Connecting line behind dots */}
              <div className="absolute top-5 left-0 w-full h-0.5 bg-gray-200 rounded-full">
                <div
                  className={`h-0.5 bg-gradient-to-r ${phase.color} rounded-full transition-all duration-500`}
                  style={{
                    width: phaseSteps.length > 1
                      ? `${((currentStep - phaseSteps[0].globalIndex) / (phaseSteps.length - 1)) * 100}%`
                      : '100%',
                  }}
                />
              </div>

              {phaseSteps.map(({ step, globalIndex }) => {
                const isCurrentDot = globalIndex === currentStep;
                const isDone = globalIndex < currentStep;
                const StepIcon = step.icon;

                return (
                  <button
                    key={step.id}
                    type="button"
                    onClick={() => onStepClick(globalIndex)}
                    title={step.title}
                    className={`
                      relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-2
                      transition-all duration-200 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-offset-2
                      ${isDone
                        ? 'bg-green-500 border-green-500 text-white shadow-md'
                        : isCurrentDot
                          ? `bg-white border-2 shadow-lg ${phase.id === 1 ? 'border-blue-500 text-blue-600' : phase.id === 2 ? 'border-green-500 text-green-600' : 'border-amber-500 text-amber-600'}`
                          : 'bg-white border-gray-300 text-gray-400'
                      }
                    `}
                  >
                    {isDone ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <StepIcon className="h-4 w-4" />
                    )}
                  </button>
                );
              })}
            </div>
          );
        })}

      {/* Step label below dots */}
      {phases
        .filter((p) => p.id === activePhaseId)
        .map((phase) => {
          const phaseSteps = getPhaseSteps(phase);
          const currentPhaseStep = phaseSteps.find(({ globalIndex }) => globalIndex === currentStep);
          if (!currentPhaseStep) return null;
          const positionInPhase = phaseSteps.findIndex(({ globalIndex }) => globalIndex === currentStep) + 1;

          return (
            <p key={phase.id} className="text-center text-xs text-gray-400 mt-3">
              {phase.name} · Step {positionInPhase} of {phaseSteps.length}
            </p>
          );
        })}
    </div>
  );
};

export default PhaseTabBar;
