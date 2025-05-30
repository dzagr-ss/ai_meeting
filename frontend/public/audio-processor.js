// audio-processor.js - AudioWorklet processor for real-time audio processing

class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bufferSize = 4096;
        this.buffer = new Float32Array(this.bufferSize);
        this.bufferIndex = 0;
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        
        if (input && input.length > 0) {
            const inputChannel = input[0]; // Get the first channel
            
            // Process each sample
            for (let i = 0; i < inputChannel.length; i++) {
                this.buffer[this.bufferIndex] = inputChannel[i];
                this.bufferIndex++;
                
                // When buffer is full, send it to the main thread
                if (this.bufferIndex >= this.bufferSize) {
                    // Create a copy of the buffer to send
                    const audioData = new Float32Array(this.buffer);
                    
                    // Send the audio data to the main thread
                    this.port.postMessage({
                        type: 'audio_data',
                        audioData: audioData
                    });
                    
                    // Reset buffer
                    this.bufferIndex = 0;
                }
            }
        }
        
        // Keep the processor alive
        return true;
    }
}

// Register the processor
registerProcessor('audio-processor', AudioProcessor); 