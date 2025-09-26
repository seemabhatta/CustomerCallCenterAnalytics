import { SystemConfiguration } from '@/types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || '';

/**
 * Fetch system configuration from the backend.
 * Uses NO FALLBACK principle - fails fast if configuration unavailable.
 */
export async function fetchSystemConfiguration(): Promise<SystemConfiguration> {
  const response = await fetch(`${API_BASE_URL}/api/v1/config`);

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Configuration fetch failed: ${response.status} - ${error}`);
  }

  const config: SystemConfiguration = await response.json();

  // Validate required structure (fail fast)
  if (!config.roles || Object.keys(config.roles).length === 0) {
    throw new Error('Invalid configuration: No roles defined');
  }

  if (!config.settings) {
    throw new Error('Invalid configuration: No settings defined');
  }

  return config;
}

/**
 * Get available modes for a specific role from configuration.
 */
export function getModesForRole(config: SystemConfiguration, role: string): string[] {
  const roleConfig = config.roles[role];
  if (!roleConfig || !roleConfig.modes) {
    return [];
  }
  return Object.keys(roleConfig.modes);
}

/**
 * Get display name for a role/mode combination.
 */
export function getDisplayName(config: SystemConfiguration, role: string, mode?: string): string {
  const roleConfig = config.roles[role];
  if (!roleConfig) {
    return `${role} Assistant`;
  }

  const baseName = roleConfig.display_name;

  // Add mode suffix if not default mode
  if (mode && mode !== config.settings.default_mode) {
    const modeDisplay = mode.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    return `${baseName} (${modeDisplay} Mode)`;
  }

  return baseName;
}

/**
 * Get description for a specific mode.
 */
export function getModeDescription(config: SystemConfiguration, role: string, mode: string): string {
  const roleConfig = config.roles[role];
  if (!roleConfig || !roleConfig.modes || !roleConfig.modes[mode]) {
    return '';
  }
  return roleConfig.modes[mode].description;
}

/**
 * Get icon name for a specific mode.
 */
export function getModeIcon(config: SystemConfiguration, role: string, mode: string): string {
  const roleConfig = config.roles[role];
  if (!roleConfig || !roleConfig.modes || !roleConfig.modes[mode]) {
    return 'User'; // Default icon
  }
  return roleConfig.modes[mode].icon;
}

/**
 * Get quick actions for a specific role and mode.
 */
export function getQuickActions(config: SystemConfiguration, role: string, mode: string): import('../types').QuickAction[] {
  const roleConfig = config.roles[role];
  if (!roleConfig || !roleConfig.modes || !roleConfig.modes[mode]) {
    return [];
  }
  return roleConfig.modes[mode].quick_actions || [];
}