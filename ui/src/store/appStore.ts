import { create } from 'zustand';
import type { Message } from '../components/MessageArea';

interface Channel {
  id: string;
  name: string;
  ttsEnabled: boolean;
  threads: { id: string; title: string }[];
}

interface AppState {
  channels: Channel[];
  activeChannelId: string | null;
  messages: Record<string, Message[]>;  // channelId -> messages
  voiceState: string;
  theme: string;
  connected: boolean;

  setChannels: (channels: Channel[]) => void;
  setActiveChannel: (id: string) => void;
  addMessage: (channelId: string, message: Message) => void;
  setVoiceState: (state: string) => void;
  setTheme: (theme: string) => void;
  setConnected: (connected: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  channels: [],
  activeChannelId: null,
  messages: {},
  voiceState: 'idle',
  theme: 'dark',
  connected: false,

  setChannels: (channels) => set({ channels }),
  setActiveChannel: (id) => set({ activeChannelId: id }),
  addMessage: (channelId, message) => set((state) => ({
    messages: {
      ...state.messages,
      [channelId]: [...(state.messages[channelId] || []), message],
    },
  })),
  setVoiceState: (voiceState) => set({ voiceState }),
  setTheme: (theme) => set({ theme }),
  setConnected: (connected) => set({ connected }),
}));
