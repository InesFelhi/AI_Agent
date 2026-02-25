# DNS Lookup Stage

## Summary

-   **Internal name**: `DnsLookup`
-   **Category**: Communication
-   **Purpose**: Resolve a domain name to an IP address using configurable DNS resolution strategies (IPv4 only, IPv6 only, IPv6 with IPv4 fallback, or Happy Eyeballs).

------------------------------------------------------------------------

## Compatibility

-   **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`

-   **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`

-   **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`

-   **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`

-   **Required permissions**:

    -   `INTERNET`
    -   `ACCESS_NETWORK_STATE`

------------------------------------------------------------------------

# Input parameters

| Parameter | Type | Required | Possible values | Android Compatibility | AndroMate Compatibility | Default |
|-----------|------|----------|-----------------|----------------------|-------------------------|---------|
| `url` | String | Yes | Valid domain or IP | {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | — |
| `dns_server` | String | No | Valid DNS server IP | {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | 8.8.8.8 (Google DNS) |
| `resolve_ops` | String | Yes | FORCE_IPV4, FORCE_IPV6, PREFER_IPV6_FALLBACK_IPV4, HAPPY_EYEBALLS | {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | PREFER_IPV6_FALLBACK_IPV4 |

------------------------------------------------------------------------

# Output parameters

| Field | Type | Trigger condition | Android Compatibility | AndroMate Compatibility | Default |
|-------|------|------------------|----------------------|-------------------------|---------|
| `dns_result_output` | String | When DNS resolution succeeds | {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | `<ANDROMATE_NULL_VALUE>` |

------------------------------------------------------------------------

## Exceptions

| Code | Exception Name | Description |
|------|---------------|-------------|
| DNS_LOOKUP_EMPTY_URL | Empty URL | The domain/URL field is empty or null. |
| DNS_LOOKUP_FAILED | DNS Resolution Failed | DNS lookup failed for the given domain (no A/AAAA records found or DNS server error). |
| DNS_LOOKUP_TIMEOUT | DNS Timeout | DNS resolution exceeded the 5-second timeout. |
| DNS_LOOKUP_INVALID_STRATEGY | Invalid Strategy | The specified resolution strategy is not recognized. |

------------------------------------------------------------------------

# Flowchart

The following diagram illustrates the overall implementation based on Android code:

```mermaid
flowchart TD
    Start([Start DnsLookupTask]) --> ResolveParams[🔄 Resolve Parameters<br/>URL, DNS server, strategy]
    
    ResolveParams --> ValidateURL{URL<br/>empty ?}
    
    ValidateURL -->|Yes| E1[❌ DNS_LOOKUP_EMPTY_URL]
    ValidateURL -->|No| CheckIP{Already<br/>IP address ?}
    
    CheckIP -->|Yes| ReturnIP[📍 Return IP directly<br/>No DNS needed]
    CheckIP -->|No| Strategy{Resolution<br/>Strategy}
    
    Strategy -->|FORCE_IPV4| ForceIPV4[🔍 Query A records only]
    Strategy -->|FORCE_IPV6| ForceIPV6[🔍 Query AAAA records only]
    Strategy -->|PREFER_IPV6_FALLBACK_IPV4| PreferIPV6[🔄 Try IPv6 first<br/>fallback to IPv4]
    Strategy -->|HAPPY_EYEBALLS| HappyEyeballs[⚡ RFC 8305<br/>concurrent IPv6 + IPv4]
    
    ForceIPV4 --> DNSQuery[📡 DNS Query<br/>Timeout: 5000ms]
    ForceIPV6 --> DNSQuery
    PreferIPV6 --> DNSQuery
    HappyEyeballs --> DNSQuery
    
    ReturnIP --> StoreResult[💾 Store Result<br/>StrTaskResult]
    
    DNSQuery -->|Success| GetIP[📥 Get IP Address<br/>First result only]
    DNSQuery -->|Timeout| E3[❌ DNS_LOOKUP_TIMEOUT]
    DNSQuery -->|Failed| E2[❌ DNS_LOOKUP_FAILED]
    
    GetIP --> StoreResult
    
    StoreResult --> LogReport[📋 Log Report<br/>ReportSection]
    
    LogReport --> Success([✅ Success])
    
    E1 --> Error([❌ Exception])
    E2 --> Error
    E3 --> Error
    
    style Start fill:#e3f2fd
    style Success fill:#c8e6c9
    style Error fill:#ffcdd2
    style ResolveParams fill:#fff9c4
    style DNSQuery fill:#f3e5f5
    style StoreResult fill:#c8e6c9
    style E1 fill:#ffcdd2
    style E2 fill:#ffcdd2
    style E3 fill:#ffcdd2
```

**How it works:**

1. **Resolve parameters**: Resolves dynamic variables in URL and DNS server
2. **Validate URL**: Checks that URL is not empty
3. **Check if already IP**: If the input is already an IP address, return it directly without DNS query
4. **Select resolution strategy**: Chooses between FORCE_IPV4, FORCE_IPV6, PREFER_IPV6_FALLBACK_IPV4, or HAPPY_EYEBALLS
5. **DNS Query**: Performs DNS lookup with 5-second timeout
6. **Get IP Address**: Extracts the first IP from results
7. **Store result**: Saves the resolved IP in StrTaskResult
8. **Log report**: Records execution report
9. **Result**: Returns success or exception

------------------------------------------------------------------------

# DNS Resolution Strategies

## Strategy 1: FORCE_IPV4

```mermaid
sequenceDiagram
    participant App as DnsLookupTask
    participant DNS as DNS Server
    participant Result as StrTaskResult

    App->>DNS: Query A records (IPv4)<br/>domain + timeout 5s
    DNS-->>App: A Record(s) found
    App->>App: Extract first IPv4
    App->>Result: Store IPv4 address
    Result-->>App: Success

    Alt No A records
        DNS-->>App: No records
        App->>App: Throw DNS_LOOKUP_FAILED
    End

    Alt Timeout
        DNS-->>App: Timeout
        App->>App: Throw DNS_LOOKUP_TIMEOUT
    End
```

**Use case**: Force resolution to IPv4 only (legacy systems).

---

## Strategy 2: FORCE_IPV6

```mermaid
sequenceDiagram
    participant App as DnsLookupTask
    participant DNS as DNS Server
    participant Result as StrTaskResult

    App->>DNS: Query AAAA records (IPv6)<br/>domain + timeout 5s
    DNS-->>App: AAAA Record(s) found
    App->>App: Extract first IPv6
    App->>Result: Store IPv6 address
    Result-->>App: Success

    Alt No AAAA records
        DNS-->>App: No records
        App->>App: Throw DNS_LOOKUP_FAILED
    End

    Alt Timeout
        DNS-->>App: Timeout
        App->>App: Throw DNS_LOOKUP_TIMEOUT
    End
```

**Use case**: Force resolution to IPv6 only (modern IPv6-only networks).

---

## Strategy 3: PREFER_IPV6_FALLBACK_IPV4

```mermaid
sequenceDiagram
    participant App as DnsLookupTask
    participant DNS as DNS Server
    participant Result as StrTaskResult

    App->>DNS: Query AAAA records (IPv6)<br/>timeout 5s
    DNS-->>App: Response (AAAA or empty)

    Alt IPv6 found
        App->>Result: Store IPv6 address
        Result-->>App: Success ✅
    Else No IPv6
        App->>DNS: Query A records (IPv4)<br/>fallback
        DNS-->>App: Response (A or empty)
        
        Alt IPv4 found
            App->>Result: Store IPv4 address
            Result-->>App: Success ✅ (with fallback flag)
        Else No IPv4
            App->>App: Throw DNS_LOOKUP_FAILED
        End
    End
```

**Use case**: Prefer modern IPv6 but fallback to IPv4 if unavailable.

---

## Strategy 4: HAPPY_EYEBALLS (RFC 8305)

```mermaid
sequenceDiagram
    participant App as DnsLookupTask
    participant DNS as DNS Server
    participant IPv6Query as IPv6 Lookup
    participant IPv4Query as IPv4 Lookup
    participant Result as StrTaskResult

    App->>IPv6Query: Start IPv6 (AAAA) query<br/>timeout 5s
    Note over IPv6Query,IPv4Query: Wait 250ms
    App->>IPv4Query: Start IPv4 (A) query<br/>timeout 5s

    Par IPv6 and IPv4 race
        IPv6Query->>DNS: AAAA lookup
        IPv4Query->>DNS: A lookup
    End

    Alt First to complete wins
        Note over IPv6Query,IPv4Query: First result (IPv6 or IPv4) wins
        App->>Result: Store winning IP
        Result-->>App: Success ✅
        App->>App: Cancel slower query
    Else Both timeout
        App->>App: Throw DNS_LOOKUP_TIMEOUT
    Else Both fail
        App->>App: Throw DNS_LOOKUP_FAILED
    End
```

**Use case**: Fastest resolution with intelligent fallback (RFC 8305 standard).

---

## Strategy Comparison

| Strategy | IPv4 | IPv6 | Speed | Use Case |
|----------|------|------|-------|----------|
| **FORCE_IPV4** | ✅ | ❌ | Fast | Legacy systems |
| **FORCE_IPV6** | ❌ | ✅ | Fast | IPv6-only networks |
| **PREFER_IPV6_FALLBACK_IPV4** | ✅ (fallback) | ✅ (preferred) | Medium | Balanced modern networks |
| **HAPPY_EYEBALLS** | ✅ | ✅ | Very Fast | Optimized (RFC 8305) |

------------------------------------------------------------------------

# Parameter details

## 1. Input parameter: `url`

Domain name or IP address to resolve.

### Example

``` json
"url": "api.example.com"
```

------------------------------------------------------------------------

## 2. Input parameter: `dns_server`

Custom DNS server to use for resolution.

### Default value

`8.8.8.8` (Google DNS)

### Possible values

- `8.8.8.8` (Google)
- `1.1.1.1` (Cloudflare)
- `208.67.222.222` (OpenDNS)
- Custom DNS server IP

### Example

``` json
"dns_server": "1.1.1.1"
```

------------------------------------------------------------------------

## 3. Input parameter: `resolve_ops`

Resolution strategy to use.

### Possible values

- `FORCE_IPV4`: Query A records only
- `FORCE_IPV6`: Query AAAA records only
- `PREFER_IPV6_FALLBACK_IPV4`: Try IPv6 first, fallback to IPv4
- `HAPPY_EYEBALLS`: RFC 8305 concurrent resolution

### Default value

`PREFER_IPV6_FALLBACK_IPV4`

### Example

``` json
"resolve_ops": "HAPPY_EYEBALLS"
```

------------------------------------------------------------------------

# Output details

## 1. Result variable: `dns_result_output`

Contains the resolved IP address (IPv4 or IPv6).

### Example

``` json
"dns_result_output": "$DNS_IP"
```

------------------------------------------------------------------------

# Complete JSON example

``` json
{
  "DnsLookup": [
    {
      "id": "-1",
      "title": "DNS Lookup Stage",
      "url": "api.example.com",
      "dns_server": "8.8.8.8",
      "resolve_ops": "HAPPY_EYEBALLS",
      "dns_result_output": "$RESOLVED_IP"
    }
  ]
}
```

------------------------------------------------------------------------

# Notes

-   **Timeout**: All DNS queries have a fixed 5-second timeout.
-   **Already IP**: If the input is already an IP address (IPv4 or IPv6), no DNS query is performed and the address is returned immediately.
-   **Happy Eyeballs**: Implements RFC 8305 with 250ms stagger between IPv6 and IPv4 queries for optimal performance.
-   **DNS Server**: If not specified, the system default DNS server is used (usually from device settings).

------------------------------------------------------------------------

# IP Address Verification

AndroMate uses the following regex patterns to check if the URL is already a valid IP address:

## IPv4 Regex

```regex
^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$
```

## IPv6 Regex

```regex
^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:))$
```

If the URL matches one of these regex patterns, no DNS query is performed and the IP address is returned directly.




