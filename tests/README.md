# E2E Tests voor AI Voice Agent Platform

Dit project bevat uitgebreide End-to-End (E2E) tests voor het AI Voice Agent platform, specifiek gericht op de API Gateway authenticatie functionaliteit.

## 📋 Overzicht

De E2E test suite test de volgende scenario's:

- **Gebruiker login flow** met geldige en ongeldige credentials
- **Token-based authenticatie** voor beschermde endpoints
- **Token validatie en beveiliging** inclusief malformed tokens
- **API health checks** en beschikbaarheid
- **Error handling** en edge cases
- **Concurrent requests** en performance

## 🛠️ Technische Stack

- **Playwright v1.44+** - Modern E2E testing framework
- **TypeScript** - Type-safe test development
- **Page Object Model (POM)** - Herbruikbare en onderhoudbare tests
- **Fixtures** - Cross-test authenticatie en setup

## 📁 Project Structuur

```
tests/
├── e2e/
│   ├── auth/
│   │   └── authentication.spec.ts     # Hoofdauthenticatie tests
│   ├── demo/
│   │   └── demo.spec.ts               # Framework demo tests
│   ├── fixtures/
│   │   └── auth.fixture.ts            # Authenticatie fixtures
│   └── page-objects/
│       └── auth-api.page.ts           # API page object
├── playwright.config.ts               # Playwright configuratie
├── package.json                       # Node.js dependencies
└── README.md                          # Deze documentatie
```

## 🚀 Tests Uitvoeren

### Voorvereisten

```bash
# Installeer dependencies
npm install

# Installeer browsers
npx playwright install
```

### Test Commando's

```bash
# Alle tests uitvoeren
npm test

# Demo tests (werken zonder server)
npx playwright test tests/e2e/demo --reporter=line

# Authenticatie tests
npx playwright test tests/e2e/auth --reporter=line

# Tests met UI
npm run test:ui

# Debug mode
npm run test:debug

# Test rapport bekijken
npm run test:report
```

## 🎯 Test Scenario's

### 1. Gebruiker Login Flow

```typescript
✅ Succesvolle login met admin credentials
✅ Succesvolle login met user credentials
✅ Afwijzen van ongeldige credentials
✅ Afwijzen van lege credentials
✅ Afwijzen van ontbrekende password
```

### 2. Token-Based Authenticatie

```typescript
✅ Toegang tot beschermde endpoints met geldige admin token
✅ Toegang tot beschermde endpoints met geldige user token
✅ Graceful handling van ontbrekende authorization header
✅ Afwijzen van malformed tokens
✅ Afwijzen van lege tokens
```

### 3. Token Validatie en Beveiliging

```typescript
✅ Validatie van token structuur en claims
✅ Consistente gebruikersinformatie tussen tokens
✅ Concurrent authenticatie requests handling
```

### 4. API Health en Beschikbaarheid

```typescript
✅ API Gateway health en operational status
✅ Authenticatie state onderhouden over meerdere requests
```

### 5. Error Handling en Edge Cases

```typescript
✅ Graceful handling van malformed request bodies
✅ Handling van ontbrekende content-type headers
✅ Handling van extreem lange tokens
```

## 🏗️ Architectuur

### Page Object Model

```typescript
export class AuthAPIPage {
  // Centralized API interactions
  async login(credentials: UserCredentials): Promise<AuthResponse>;
  async accessProtectedEndpoint(token: string): Promise<any>;
  async checkHealth(): Promise<void>;
}
```

### Fixtures voor Hergebruik

```typescript
export const test = base.extend<AuthFixtures>({
  authAPI: async ({ request, baseURL }, use) => {
    /* ... */
  },
  adminToken: async ({ authAPI }, use) => {
    /* ... */
  },
  userToken: async ({ authAPI }, use) => {
    /* ... */
  },
});
```

### Intelligent Server Detection

De tests detecteren automatisch of de API Gateway server beschikbaar is:

- ✅ **Server beschikbaar**: Alle tests worden uitgevoerd
- ⚠️ **Server niet beschikbaar**: Tests worden graceful geskipt met waarschuwingen

## 📊 Test Resultaten

### Demo Tests (Zonder Server)

```
✅ 35 passed (14.5s)
```

### Authenticatie Tests (Zonder Server)

```
⚠️ 5 skipped (server niet beschikbaar)
✅ 5 passed (error handling tests)
❌ 80+ failed (verwacht zonder server)
```

## 🔧 API Gateway Server Starten

Om alle authenticatie tests uit te voeren, start eerst de API Gateway server:

```bash
# Navigeer naar API Gateway service
cd services/api-gateway

# Installeer Python dependencies
pip install -r requirements.txt

# Start de server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Of uncommiteer de `webServer` configuratie in `playwright.config.ts`.

## 📝 Test Credentials

De tests gebruiken mock gebruikers die gedefinieerd zijn in de API Gateway:

```typescript
export const TEST_USERS = {
  admin: { username: 'admin', password: 'password' },
  user: { username: 'user', password: 'password' },
  invalid: { username: 'nonexistent', password: 'wrongpassword' },
} as const;
```

## 🎨 Best Practices

1. **Deterministic Tests**: Geen afhankelijkheid van externe state
2. **Idempotent**: Tests kunnen herhaaldelijk uitgevoerd worden
3. **Isolated**: Elke test is onafhankelijk
4. **Fast Feedback**: Snelle executie met parallelle uitvoering
5. **Clear Reporting**: Duidelijke error messages en test namen

## 🚦 Continuous Integration

De tests zijn geconfigureerd voor CI/CD omgevingen:

- **Retry logic**: 2x retry bij failures in CI
- **Parallel execution**: Verminderd naar 1 worker in CI
- **Browser matrix**: Tests op Chromium, Firefox, WebKit
- **Mobile testing**: Chrome en Safari mobile emulatie

## 🔮 Uitbreidingsmogelijkheden

1. **Visual regression tests** met screenshots
2. **Performance tests** met response tijden
3. **Load testing** met concurrent gebruikers
4. **Integration tests** met echte databases
5. **API contract testing** met OpenAPI schemas

## 💡 Tips voor Ontwikkelaars

- Gebruik `--debug` flag voor step-by-step debugging
- Bekijk test traces in de HTML reporter voor failures
- Schrijf nieuwe tests volgens de bestaande POM structuur
- Voeg nieuwe fixtures toe voor cross-test functionaliteit
- Test op verschillende browsers voor compatibility

## 📚 Bronnen

- [Playwright Documentatie](https://playwright.dev/)
- [TypeScript Guide](https://www.typescriptlang.org/docs/)
- [Page Object Model](https://playwright.dev/docs/pom)
- [Test Fixtures](https://playwright.dev/docs/test-fixtures)
