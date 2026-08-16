/**
 * Física Web — camada compartilhada de sensores do dispositivo.
 *
 * Mantém a aquisição independente dos experimentos para que queda livre,
 * MRU/MRUV, plano inclinado, elevador, movimento circular e outros possam
 * reutilizar o mesmo contrato de dados.
 *
 * Contrato principal:
 *   startMotion() -> Promise<capabilities>
 *   stopMotion()
 *   onMotion(callback) -> unsubscribe
 *
 * Cada leitura de movimento contém:
 *   timestamp, elapsed, acceleration, accelerationIncludingGravity,
 *   rotationRate e interval.
 *
 * A camada não calcula grandezas físicas específicas do experimento.
 * Conversão, calibração e análise permanecem no núcleo científico.
 */
(function (global) {
  "use strict";

  const listeners = new Set();
  let listening = false;
  let startedAt = null;

  function numberOrNull(value) {
    return Number.isFinite(Number(value)) ? Number(value) : null;
  }

  function vector(source) {
    if (!source) return { x: null, y: null, z: null };
    return {
      x: numberOrNull(source.x),
      y: numberOrNull(source.y),
      z: numberOrNull(source.z),
    };
  }

  function readMotionEvent(event) {
    const now = Date.now();
    if (startedAt === null) startedAt = now;

    return {
      timestamp: new Date(now).toISOString(),
      elapsed: (now - startedAt) / 1000,
      acceleration: vector(event.acceleration),
      accelerationIncludingGravity: vector(event.accelerationIncludingGravity),
      rotationRate: {
        alpha: numberOrNull(event.rotationRate && event.rotationRate.alpha),
        beta: numberOrNull(event.rotationRate && event.rotationRate.beta),
        gamma: numberOrNull(event.rotationRate && event.rotationRate.gamma),
      },
      interval: numberOrNull(event.interval),
    };
  }

  function emit(reading) {
    listeners.forEach(function (listener) {
      try {
        listener(reading);
      } catch (error) {
        // Um consumidor com erro não deve interromper a aquisição dos demais.
        setTimeout(function () { throw error; }, 0);
      }
    });
  }

  function handleMotion(event) {
    if (!listening) return;
    emit(readMotionEvent(event));
  }

  async function requestMotionPermission() {
    if (typeof DeviceMotionEvent === "undefined") {
      throw new Error("Este dispositivo ou navegador não oferece DeviceMotion.");
    }

    if (typeof DeviceMotionEvent.requestPermission === "function") {
      const result = await DeviceMotionEvent.requestPermission();
      if (result !== "granted") {
        throw new Error("Permissão de movimento não concedida.");
      }
    }
  }

  async function startMotion() {
    if (listening) return capabilities();

    await requestMotionPermission();
    startedAt = null;
    listening = true;
    window.addEventListener("devicemotion", handleMotion, { passive: true });
    return capabilities();
  }

  function stopMotion() {
    if (!listening) return;
    listening = false;
    window.removeEventListener("devicemotion", handleMotion);
    startedAt = null;
  }

  function onMotion(callback) {
    if (typeof callback !== "function") {
      throw new TypeError("onMotion exige uma função de callback.");
    }
    listeners.add(callback);
    return function unsubscribe() {
      listeners.delete(callback);
    };
  }

  function capabilities() {
    return {
      motion: typeof DeviceMotionEvent !== "undefined",
      orientation: typeof DeviceOrientationEvent !== "undefined",
      permissionRequired: typeof DeviceMotionEvent !== "undefined" &&
        typeof DeviceMotionEvent.requestPermission === "function",
      secureContext: global.isSecureContext === true,
    };
  }

  function isRunning() {
    return listening;
  }

  global.FisicaWebSensors = Object.freeze({
    startMotion,
    stopMotion,
    onMotion,
    capabilities,
    isRunning,
  });
})(window);
