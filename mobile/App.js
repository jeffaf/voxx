/**
 * VOXX Mobile App
 * Voice-controlled coding assistant for Android
 */

import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Audio } from 'expo-av';
import * as Speech from 'expo-speech';

// Configuration
const SERVER_URL = 'http://100.76.158.67:8000';
const MAX_HISTORY_ITEMS = 10;

export default function App() {
  // State
  const [recording, setRecording] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [transcription, setTranscription] = useState('');
  const [response, setResponse] = useState('');
  const [agentCount, setAgentCount] = useState(null);
  const [executionTime, setExecutionTime] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('unknown'); // green, yellow, red
  const [commandHistory, setCommandHistory] = useState([]);
  const [permissionGranted, setPermissionGranted] = useState(false);

  // Request microphone permissions on mount
  useEffect(() => {
    requestPermissions();
    checkServerConnection();
  }, []);

  /**
   * Request microphone permissions
   */
  const requestPermissions = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      setPermissionGranted(status === 'granted');

      if (status !== 'granted') {
        Alert.alert(
          'Microphone Permission Required',
          'VOXX needs microphone access to record voice commands.',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      console.error('Permission error:', error);
      Alert.alert('Error', 'Failed to request microphone permissions');
    }
  };

  /**
   * Check server connection status
   */
  const checkServerConnection = async () => {
    try {
      const response = await fetch(`${SERVER_URL}/`, { timeout: 5000 });
      if (response.ok) {
        setConnectionStatus('green');
      } else {
        setConnectionStatus('yellow');
      }
    } catch (error) {
      console.error('Connection check failed:', error);
      setConnectionStatus('red');
    }
  };

  /**
   * Start recording audio
   */
  const startRecording = async () => {
    if (!permissionGranted) {
      Alert.alert('Permission Denied', 'Microphone permission is required');
      return;
    }

    try {
      // Configure audio mode
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Start recording with high quality
      const { recording: newRecording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );

      setRecording(newRecording);
      setIsRecording(true);
      setTranscription('');
      setResponse('');
      setAgentCount(null);
      setExecutionTime(null);

      // Voice feedback
      Speech.speak('Recording', { rate: 1.2 });

      console.log('Recording started');
    } catch (error) {
      console.error('Failed to start recording:', error);
      Alert.alert('Error', `Failed to start recording: ${error.message}`);
    }
  };

  /**
   * Stop recording and process audio
   */
  const stopRecording = async () => {
    if (!recording) return;

    try {
      setIsRecording(false);
      Speech.speak('Processing', { rate: 1.2 });

      console.log('Stopping recording...');
      await recording.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: false,
      });

      const uri = recording.getURI();
      console.log('Recording stopped, URI:', uri);

      setRecording(null);

      // Send to server
      await sendAudioToServer(uri);

    } catch (error) {
      console.error('Failed to stop recording:', error);
      Alert.alert('Error', `Failed to stop recording: ${error.message}`);
      setIsRecording(false);
      setIsProcessing(false);
    }
  };

  /**
   * Send audio file to server via WebSocket for streaming processing
   */
  const sendAudioToServer = async (audioUri, retryCount = 0) => {
    const MAX_RETRIES = 3;
    setIsProcessing(true);
    setResponse('');
    setTranscription('');
    setStatusMessage('Connecting...');

    try {
      // Read audio file as blob
      const response = await fetch(audioUri);
      const blob = await response.blob();
      const arrayBuffer = await blob.arrayBuffer();

      console.log('Connecting to WebSocket...');

      // Connect to WebSocket
      const ws = new WebSocket(SERVER_URL.replace('http://', 'ws://').replace('https://', 'wss://') + '/ws/voice');

      // Set up message handler
      ws.onopen = () => {
        console.log('WebSocket connected, sending audio...');
        setStatusMessage('Sending audio...');

        // Send audio data
        ws.send(arrayBuffer);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);

        switch (data.type) {
          case 'connected':
            setStatusMessage(data.message);
            setConnectionStatus('green');
            break;

          case 'status':
            setStatusMessage(data.message);
            break;

          case 'transcription':
            setTranscription(data.text);
            setStatusMessage('Got transcription!');
            break;

          case 'complexity':
            setAgentCount(data.level);
            break;

          case 'response_chunk':
            // Append streaming response chunks
            setResponse((prev) => prev + data.text + '\n');
            break;

          case 'complete':
            setStatusMessage('Complete!');
            setExecutionTime(data.execution_time);
            setIsProcessing(false);

            // Add to history
            addToHistory({
              command: transcription,
              success: data.success,
              agentCount: data.complexity || 'standard',
              time: data.execution_time,
              timestamp: new Date().toLocaleTimeString(),
            });

            // Speak full response
            if (response) {
              Speech.speak(response, { rate: 1.1 });
            }

            ws.close();
            break;

          case 'error':
            setStatusMessage('Error!');
            Alert.alert('Error', data.message);
            setResponse('Error: ' + data.message);
            setIsProcessing(false);
            setConnectionStatus('red');
            ws.close();
            break;
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatusMessage('Connection error!');

        // Retry logic
        if (retryCount < MAX_RETRIES) {
          console.log(`Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
          setTimeout(() => {
            sendAudioToServer(audioUri, retryCount + 1);
          }, 1000);
        } else {
          setConnectionStatus('red');
          Alert.alert(
            'Connection Failed',
            `Could not connect to server after ${MAX_RETRIES} attempts. Check Tailscale connection.`
          );
          setIsProcessing(false);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
      };

    } catch (error) {
      console.error('Audio processing failed:', error);
      setStatusMessage('Error!');

      // Retry logic
      if (retryCount < MAX_RETRIES) {
        console.log(`Retrying... (${retryCount + 1}/${MAX_RETRIES})`);
        setTimeout(() => {
          sendAudioToServer(audioUri, retryCount + 1);
        }, 1000);
      } else {
        setConnectionStatus('red');
        Alert.alert('Error', error.message);
        setResponse('Error: ' + error.message);
        setIsProcessing(false);
      }
    }
  };

  /**
   * Add command to history
   */
  const addToHistory = (item) => {
    setCommandHistory((prev) => {
      const newHistory = [item, ...prev];
      return newHistory.slice(0, MAX_HISTORY_ITEMS);
    });
  };

  /**
   * Get connection status color
   */
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'green': return '#4CAF50';
      case 'yellow': return '#FFC107';
      case 'red': return '#F44336';
      default: return '#9E9E9E';
    }
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.logo}>VOXX</Text>
        <Text style={styles.subtitle}>Voice eXecution eXpress</Text>
        <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
      </View>

      {/* Main Content */}
      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>

        {/* Transcription */}
        {transcription ? (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Command</Text>
            <Text style={styles.cardText}>{transcription}</Text>
          </View>
        ) : null}

        {/* Metrics */}
        {(agentCount || executionTime) && (
          <View style={styles.metricsRow}>
            {agentCount && (
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>{agentCount}</Text>
                <Text style={styles.metricLabel}>Complexity</Text>
              </View>
            )}
            {executionTime && (
              <View style={styles.metricCard}>
                <Text style={styles.metricValue}>{executionTime}s</Text>
                <Text style={styles.metricLabel}>Time</Text>
              </View>
            )}
          </View>
        )}

        {/* Response */}
        {response ? (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Response</Text>
            <Text style={styles.responseText}>{response}</Text>
          </View>
        ) : null}

        {/* Command History */}
        {commandHistory.length > 0 && (
          <View style={styles.historySection}>
            <Text style={styles.historyTitle}>Recent Commands</Text>
            {commandHistory.map((item, index) => (
              <View key={index} style={styles.historyItem}>
                <Text style={styles.historyCommand}>{item.command}</Text>
                <View style={styles.historyMeta}>
                  <Text style={styles.historyMetaText}>
                    {item.agentCount} • {item.time}s • {item.timestamp}
                  </Text>
                  <Text style={[
                    styles.historyStatus,
                    { color: item.success ? '#4CAF50' : '#F44336' }
                  ]}>
                    {item.success ? '✓' : '✗'}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

      </ScrollView>

      {/* Recording Button */}
      <View style={styles.buttonContainer}>
        {isProcessing ? (
          <View style={styles.processingContainer}>
            <ActivityIndicator size="large" color="#00FFFF" />
            <Text style={styles.processingText}>
              {statusMessage || 'PROCESSING...'}
            </Text>
          </View>
        ) : (
          <TouchableOpacity
            style={[
              styles.recordButton,
              isRecording && styles.recordButtonActive
            ]}
            onPressIn={startRecording}
            onPressOut={stopRecording}
            disabled={!permissionGranted || isProcessing}
          >
            <View style={styles.recordButtonInner}>
              <Text style={styles.recordButtonText}>
                {isRecording ? '🎤 RECORDING' : '🎤 HOLD TO SPEAK'}
              </Text>
            </View>
          </TouchableOpacity>
        )}
      </View>

      {/* Footer */}
      <Text style={styles.footer}>
        {permissionGranted ? 'Secured via Tailscale' : 'Grant microphone permission to start'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0f',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 20,
    alignItems: 'center',
    backgroundColor: '#0f0f1a',
    borderBottomWidth: 2,
    borderBottomColor: '#FF00FF',
    shadowColor: '#FF00FF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 8,
    elevation: 8,
  },
  logo: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#00FFFF',
    letterSpacing: 8,
    textShadowColor: '#FF00FF',
    textShadowOffset: { width: 2, height: 2 },
    textShadowRadius: 8,
  },
  subtitle: {
    fontSize: 12,
    color: '#FF00FF',
    marginTop: 5,
    letterSpacing: 2,
    textTransform: 'uppercase',
  },
  statusDot: {
    position: 'absolute',
    top: 65,
    right: 20,
    width: 12,
    height: 12,
    borderRadius: 6,
    shadowColor: '#00FF00',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 8,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  card: {
    backgroundColor: '#0f0f1a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 2,
    borderColor: '#FF00FF',
    shadowColor: '#FF00FF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  cardTitle: {
    fontSize: 14,
    color: '#00FFFF',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 2,
    fontWeight: 'bold',
  },
  cardText: {
    fontSize: 18,
    color: '#fff',
    lineHeight: 24,
  },
  responseText: {
    fontSize: 16,
    color: '#E0E0FF',
    lineHeight: 22,
    fontFamily: 'monospace',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
  },
  metricCard: {
    backgroundColor: '#0f0f1a',
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
    flex: 1,
    marginHorizontal: 8,
    borderWidth: 2,
    borderColor: '#00FFFF',
    shadowColor: '#00FFFF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
  },
  metricValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FF00FF',
    textShadowColor: '#FF00FF',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10,
  },
  metricLabel: {
    fontSize: 12,
    color: '#00FFFF',
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  historySection: {
    marginTop: 8,
  },
  historyTitle: {
    fontSize: 14,
    color: '#FF00FF',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 2,
    fontWeight: 'bold',
  },
  historyItem: {
    backgroundColor: '#0f0f1a',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderLeftWidth: 4,
    borderColor: '#1a1a2e',
    borderLeftColor: '#00FFFF',
  },
  historyCommand: {
    fontSize: 14,
    color: '#fff',
    marginBottom: 6,
  },
  historyMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  historyMetaText: {
    fontSize: 11,
    color: '#888',
  },
  historyStatus: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonContainer: {
    padding: 20,
    paddingBottom: 40,
  },
  recordButton: {
    backgroundColor: '#FF00FF',
    borderRadius: 100,
    height: 120,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#00FFFF',
    shadowColor: '#FF00FF',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 20,
    elevation: 10,
  },
  recordButtonActive: {
    backgroundColor: '#00FFFF',
    borderColor: '#FF00FF',
    transform: [{ scale: 0.95 }],
    shadowColor: '#00FFFF',
  },
  recordButtonInner: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  recordButtonText: {
    color: '#0a0a0f',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 2,
    textShadowColor: '#fff',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 4,
  },
  processingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  processingText: {
    color: '#00FFFF',
    fontSize: 16,
    marginTop: 16,
    letterSpacing: 1,
    textShadowColor: '#00FFFF',
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 8,
  },
  footer: {
    textAlign: 'center',
    color: '#888',
    fontSize: 11,
    paddingBottom: 20,
  },
});
