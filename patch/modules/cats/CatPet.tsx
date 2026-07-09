/**
 * Created at: 2026-07-08 22:36 EDT
 * Created by: Codex
 * Last Modified at: 2026-07-08 22:36 EDT
 * Last Modified by: Codex
 *
 * CatPet - Main Desktop Pet Component
 *
 * Phase 2 Features:
 * - AI behavior system (idle, walk, sit, sleep, play)
 * - Random movement with boundaries
 * - Click interaction
 * - Smooth animations and transitions
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { Cat } from './components/Cat';
import { BehaviorEngine } from './engine/BehaviorEngine';
import { MovementEngine } from './engine/MovementEngine';
import type { CatPetProps, Position, CatState } from './types';
import './CatPet.css';

const GROUND_OFFSET = 150;
const DEFAULT_POSITION: Position = { x: 50, y: typeof window !== 'undefined' ? window.innerHeight - GROUND_OFFSET : 500 };
const DEFAULT_SCALE = 0.5;

export function CatPet({
  initialPosition = DEFAULT_POSITION,
  scale = DEFAULT_SCALE,
  enableDrag = true,
  enableAI = true,
  onInteraction,
}: CatPetProps = {}) {
  const location = useLocation();
  const [position, setPosition] = useState<Position>(() => ({
    x: initialPosition?.x ?? 50,
    y: initialPosition?.y ?? (typeof window !== 'undefined' ? window.innerHeight - GROUND_OFFSET : 500),
  }));
  const [isDragging, setIsDragging] = useState(false);
  const [currentAnimation, setCurrentAnimation] = useState<CatState>('idle');
  const [direction, setDirection] = useState<'left' | 'right'>('right');
  const [rotation, setRotation] = useState(0);
  const prevPath = useRef(location.pathname);

  const dragOffset = useRef<Position>({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const behaviorEngine = useRef<BehaviorEngine | null>(null);
  const movementEngine = useRef<MovementEngine | null>(null);
  const isUserInteracting = useRef(false);
  const positionRef = useRef<Position>(position);
  const directionRef = useRef<'left' | 'right'>(direction);
  const rotationRef = useRef(rotation);

  const applyPosition = useCallback((nextPosition: Position, syncReactState = false) => {
    positionRef.current = { ...nextPosition };
    if (containerRef.current) {
      containerRef.current.style.transform = `translate3d(${nextPosition.x}px, ${nextPosition.y}px, 0)`;
    }
    if (syncReactState) {
      setPosition(nextPosition);
    }
  }, []);

  useEffect(() => {
    applyPosition(position, false);
  }, [applyPosition, position]);

  const applyDirection = useCallback((nextDirection: 'left' | 'right') => {
    if (directionRef.current === nextDirection) return;
    directionRef.current = nextDirection;
    setDirection(nextDirection);
  }, []);

  const applyRotation = useCallback((nextRotation: number) => {
    if (Math.abs(rotationRef.current - nextRotation) < 0.5) return;
    rotationRef.current = nextRotation;
    setRotation(nextRotation);
  }, []);

  // Initialize engines
  useEffect(() => {
    if (!enableAI) return;

    behaviorEngine.current = new BehaviorEngine();
    movementEngine.current = new MovementEngine(position);

    const handleStateChange = (newState: CatState) => {
      setCurrentAnimation(newState);

      if (newState === 'walk' && movementEngine.current) {
        applyRotation(0);
        const target = movementEngine.current.generateRandomTarget();
        movementEngine.current.moveTo(target, (pos, dir) => {
          applyPosition(pos);
          applyDirection(dir);
        });
      } else if (newState === 'climb' && movementEngine.current) {
        const target = movementEngine.current.generateClimbTarget();
        movementEngine.current.climb(target, (pos, dir, rot) => {
          applyPosition(pos);
          applyDirection(dir);
          applyRotation(rot);  // Set rotation for climbing (90 or -90 degrees)
        });
      } else if (movementEngine.current) {
        applyRotation(0);  // Reset rotation for idle, sit, sleep, play
        movementEngine.current.stopMovement();
      }
    };

    behaviorEngine.current.start(handleStateChange);

    return () => {
      behaviorEngine.current?.destroy();
      movementEngine.current?.destroy();
    };
  }, [enableAI, applyDirection, applyPosition, applyRotation]);

  // Route change detection - trigger fall animation only if cat is in upper 3/4 of screen
  useEffect(() => {
    if (location.pathname !== prevPath.current) {
      prevPath.current = location.pathname;

      // Check if cat is in upper 3/4 of screen (needs to fall)
      const fallThreshold = window.innerHeight * 0.75;
      const shouldFall = positionRef.current.y < fallThreshold;

      // Stop AI
      behaviorEngine.current?.stop();
      movementEngine.current?.stopMovement();

      if (shouldFall) {
        // Trigger fall animation
        setCurrentAnimation('fall');

        if (movementEngine.current) {
          movementEngine.current.fall(
            (pos, rot) => {
              applyPosition(pos);
              applyRotation(rot);
            },
            () => {
              // After landing, return to idle
              applyRotation(0);
              setCurrentAnimation('idle');

              // Restart AI behavior
              if (enableAI && behaviorEngine.current) {
                const handleStateChange = (newState: CatState) => {
                  setCurrentAnimation(newState);

                  if (newState === 'walk' && movementEngine.current) {
                    applyRotation(0);
                    const target = movementEngine.current.generateRandomTarget();
                    movementEngine.current.moveTo(target, (pos, dir) => {
                      applyPosition(pos);
                      applyDirection(dir);
                    });
                  } else if (newState === 'climb' && movementEngine.current) {
                    const target = movementEngine.current.generateClimbTarget();
                    movementEngine.current.climb(target, (pos, dir, rot) => {
                      applyPosition(pos);
                      applyDirection(dir);
                      applyRotation(rot);
                    });
                  } else if (movementEngine.current) {
                    applyRotation(0);
                    movementEngine.current.stopMovement();
                  }
                };

                behaviorEngine.current.start(handleStateChange);
              }
            }
          );
        }
      } else {
        // Cat is already at bottom, just restart AI without falling
        applyRotation(0);
        setCurrentAnimation('idle');

        if (enableAI && behaviorEngine.current) {
          const handleStateChange = (newState: CatState) => {
            setCurrentAnimation(newState);

            if (newState === 'walk' && movementEngine.current) {
              applyRotation(0);
              const target = movementEngine.current.generateRandomTarget();
              movementEngine.current.moveTo(target, (pos, dir) => {
                applyPosition(pos);
                applyDirection(dir);
              });
            } else if (newState === 'climb' && movementEngine.current) {
              const target = movementEngine.current.generateClimbTarget();
              movementEngine.current.climb(target, (pos, dir, rot) => {
                applyPosition(pos);
                applyDirection(dir);
                applyRotation(rot);
              });
            } else if (movementEngine.current) {
              applyRotation(0);
              movementEngine.current.stopMovement();
            }
          };

          behaviorEngine.current.start(handleStateChange);
        }
      }
    }
  }, [location.pathname, enableAI, applyDirection, applyPosition, applyRotation]);

  // Pause AI during user interaction
  useEffect(() => {
    if (isDragging || isUserInteracting.current) {
      behaviorEngine.current?.stop();
      movementEngine.current?.stopMovement();
    } else if (enableAI && behaviorEngine.current) {
      const handleStateChange = (newState: CatState) => {
        setCurrentAnimation(newState);

        if (newState === 'walk' && movementEngine.current) {
          applyRotation(0);
          const target = movementEngine.current.generateRandomTarget();
          movementEngine.current.moveTo(target, (pos, dir) => {
            applyPosition(pos);
            applyDirection(dir);
          });
        } else if (newState === 'climb' && movementEngine.current) {
          const target = movementEngine.current.generateClimbTarget();
          movementEngine.current.climb(target, (pos, dir, rot) => {
            applyPosition(pos);
            applyDirection(dir);
            applyRotation(rot);
          });
        } else if (movementEngine.current) {
          applyRotation(0);
          movementEngine.current.stopMovement();
        }
      };

      behaviorEngine.current.start(handleStateChange);
    }
  }, [isDragging, enableAI, applyDirection, applyPosition, applyRotation]);

  // Mouse down - start dragging
  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!enableDrag) return;

      e.preventDefault();
      setIsDragging(true);
      isUserInteracting.current = true;

      const rect = containerRef.current?.getBoundingClientRect();
      if (rect) {
        dragOffset.current = {
          x: e.clientX - rect.left,
          y: e.clientY - rect.top,
        };
      }

      onInteraction?.('drag-start');
    },
    [enableDrag, onInteraction]
  );

  // Mouse move and up - dragging
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newX = e.clientX - dragOffset.current.x;
      const newY = e.clientY - dragOffset.current.y;

      applyPosition({ x: newX, y: newY });
      movementEngine.current?.setPosition({ x: newX, y: newY });
    };

    const handleMouseUp = () => {
      applyPosition(positionRef.current, true);
      movementEngine.current?.setPosition(positionRef.current);
      setIsDragging(false);
      isUserInteracting.current = false;
      onInteraction?.('drag-end');
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, onInteraction, applyPosition]);

  // Click interaction
  const handleClick = useCallback(
    (e: React.MouseEvent) => {
      if (isDragging) return;

      e.stopPropagation();
      isUserInteracting.current = true;

      if (behaviorEngine.current && movementEngine.current) {
        const shouldFall = behaviorEngine.current.handleInteraction((newState) => {
          setCurrentAnimation(newState);
        });

        // If clicked while climbing, trigger fall animation
        if (shouldFall) {
          setCurrentAnimation('fall');
          movementEngine.current.fall(
            (pos, rot) => {
              applyPosition(pos);
              applyRotation(rot);
            },
            () => {
              // After landing, return to idle
              applyRotation(0);
              setCurrentAnimation('idle');

              // Restart AI behavior
              if (enableAI && behaviorEngine.current) {
                const handleStateChange = (newState: CatState) => {
                  setCurrentAnimation(newState);

                  if (newState === 'walk' && movementEngine.current) {
                    applyRotation(0);
                    const target = movementEngine.current.generateRandomTarget();
                    movementEngine.current.moveTo(target, (pos, dir) => {
                      applyPosition(pos);
                      applyDirection(dir);
                    });
                  } else if (newState === 'climb' && movementEngine.current) {
                    const target = movementEngine.current.generateClimbTarget();
                    movementEngine.current.climb(target, (pos, dir, rot) => {
                      applyPosition(pos);
                      applyDirection(dir);
                      applyRotation(rot);
                    });
                  } else if (movementEngine.current) {
                    applyRotation(0);
                    movementEngine.current.stopMovement();
                  }
                };

                behaviorEngine.current.start(handleStateChange);
              }

              isUserInteracting.current = false;
            }
          );
        } else {
          setTimeout(() => {
            isUserInteracting.current = false;
          }, 100);
        }
      }

      onInteraction?.('click');
    },
    [isDragging, onInteraction, enableAI, applyDirection, applyPosition, applyRotation]
  );

  return (
    <div
      ref={containerRef}
      className={`cat-pet-container ${isDragging ? 'dragging' : ''}`}
      style={{
        position: 'fixed',
        left: 0,
        top: 0,
        transform: `translate3d(${positionRef.current.x}px, ${positionRef.current.y}px, 0)`,
        cursor: enableDrag ? (isDragging ? 'grabbing' : 'grab') : 'pointer',
        zIndex: 9999,
        userSelect: 'none',
      }}
      onMouseDown={handleMouseDown}
      onClick={handleClick}
    >
      <Cat animation={currentAnimation} scale={scale} direction={direction} rotation={rotation} />
    </div>
  );
}

export default CatPet;
