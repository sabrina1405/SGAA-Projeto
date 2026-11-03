export type PasswordRule = {
  label: string;
  valid: boolean;
};

export function getPasswordRules(password: string): PasswordRule[] {
  const specialCharacterCount = (password.match(/[^A-Za-z0-9\s]/g) ?? []).length;

  return [
    { label: 'Mínimo 6 caracteres', valid: password.length >= 6 },
    { label: 'Máximo 100 caracteres', valid: password.length > 0 && password.length <= 100 },
    { label: '1 caractere maiúsculo', valid: /[A-Z]/.test(password) },
    { label: '1 caractere minúsculo', valid: /[a-z]/.test(password) },
    { label: '2 caracteres especiais', valid: specialCharacterCount >= 2 },
  ];
}
