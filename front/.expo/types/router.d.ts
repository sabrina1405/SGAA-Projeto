/* eslint-disable */
import * as Router from 'expo-router';

export * from 'expo-router';

declare module 'expo-router' {
  export namespace ExpoRouter {
    export interface __routes<T extends string | object = string> {
      hrefInputParams: { pathname: Router.RelativePathString, params?: Router.UnknownInputParams } | { pathname: Router.ExternalPathString, params?: Router.UnknownInputParams } | { pathname: `/explore`; params?: Router.UnknownInputParams; } | { pathname: `/FirstAcess`; params?: Router.UnknownInputParams; } | { pathname: `/`; params?: Router.UnknownInputParams; } | { pathname: `/PasswordRec`; params?: Router.UnknownInputParams; } | { pathname: `/Tela_Inicial`; params?: Router.UnknownInputParams; } | { pathname: `/_sitemap`; params?: Router.UnknownInputParams; } | { pathname: `${'/(tabs)'}/Login` | `/Login`; params?: Router.UnknownInputParams; };
      hrefOutputParams: { pathname: Router.RelativePathString, params?: Router.UnknownOutputParams } | { pathname: Router.ExternalPathString, params?: Router.UnknownOutputParams } | { pathname: `/explore`; params?: Router.UnknownOutputParams; } | { pathname: `/FirstAcess`; params?: Router.UnknownOutputParams; } | { pathname: `/`; params?: Router.UnknownOutputParams; } | { pathname: `/PasswordRec`; params?: Router.UnknownOutputParams; } | { pathname: `/Tela_Inicial`; params?: Router.UnknownOutputParams; } | { pathname: `/_sitemap`; params?: Router.UnknownOutputParams; } | { pathname: `${'/(tabs)'}/Login` | `/Login`; params?: Router.UnknownOutputParams; };
      href: Router.RelativePathString | Router.ExternalPathString | `/explore${`?${string}` | `#${string}` | ''}` | `/FirstAcess${`?${string}` | `#${string}` | ''}` | `/${`?${string}` | `#${string}` | ''}` | `/PasswordRec${`?${string}` | `#${string}` | ''}` | `/Tela_Inicial${`?${string}` | `#${string}` | ''}` | `/_sitemap${`?${string}` | `#${string}` | ''}` | `${'/(tabs)'}/Login${`?${string}` | `#${string}` | ''}` | `/Login${`?${string}` | `#${string}` | ''}` | { pathname: Router.RelativePathString | Router.ExternalPathString | `/explore` | `/FirstAcess` | `/` | `/PasswordRec` | `/Tela_Inicial` | `/_sitemap` | `${'/(tabs)'}/Login` | `/Login`; params?: Router.UnknownInputParams; };
    }
  }
}
