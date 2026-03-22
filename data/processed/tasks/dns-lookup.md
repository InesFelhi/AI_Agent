# DNS Lookup Stage

## Summary

- **Internal name**: `DnsLookup`
- **Category**: Communication
- **Purpose**: Resolve a domain name to an IP address using configurable DNS resolution strategies (IPv4 only, IPv6 only, IPv6 with IPv4 fallback, or Happy Eyeballs).

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**:
  - `INTERNET`
  - `ACCESS_NETWORK_STATE`

# Input parameters

- Parameter: `url` | Type: String | Required: Yes | Possible values: Valid domain or IP | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: —
- Parameter: `dns_server` | Type: String | Required: No | Possible values: Valid DNS server IP | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: 8.8.8.8 (Google DNS)
- Parameter: `resolve_ops` | Type: String | Required: Yes | Possible values: FORCE_IPV4, FORCE_IPV6, PREFER_IPV6_FALLBACK_IPV4, HAPPY_EYEBALLS | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: PREFER_IPV6_FALLBACK_IPV4

# Output parameters

- Field: `dns_result_output` | Type: String | Trigger condition: When DNS resolution succeeds | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: DNS_LOOKUP_EMPTY_URL | Exception Name: Empty URL | Description: The domain/URL field is empty or null.
- Code: DNS_LOOKUP_FAILED | Exception Name: DNS Resolution Failed | Description: DNS lookup failed for the given domain (no A/AAAA records found or DNS server error).
- Code: DNS_LOOKUP_TIMEOUT | Exception Name: DNS Timeout | Description: DNS resolution exceeded the 5-second timeout.
- Code: DNS_LOOKUP_INVALID_STRATEGY | Exception Name: Invalid Strategy | Description: The specified resolution strategy is not recognized.

# Flowchart

The following diagram illustrates the overall implementation based on Android code:

Diagram Nodes:
- ResolveParams: 🔄 Resolve Parameters URL, DNS server, strategy
- E1: ❌ DNS_LOOKUP_EMPTY_URL
- ReturnIP: 📍 Return IP directly No DNS needed
- ForceIPV4: 🔍 Query A records only
- ForceIPV6: 🔍 Query AAAA records only
- PreferIPV6: 🔄 Try IPv6 first fallback to IPv4
- HappyEyeballs: ⚡ RFC 8305 concurrent IPv6 + IPv4
- DNSQuery: 📡 DNS Query Timeout: 5000ms
- StoreResult: 💾 Store Result StrTaskResult
- GetIP: 📥 Get IP Address First result only
- E3: ❌ DNS_LOOKUP_TIMEOUT
- E2: ❌ DNS_LOOKUP_FAILED
- LogReport: 📋 Log Report ReportSection

Workflow Flow:
- 🔄 Resolve Parameters URL, DNS server, strategy → ValidateURL
- 🔍 Query A records only → 📡 DNS Query Timeout: 5000ms
- 🔍 Query AAAA records only → 📡 DNS Query Timeout: 5000ms
- 🔄 Try IPv6 first fallback to IPv4 → 📡 DNS Query Timeout: 5000ms
- ⚡ RFC 8305 concurrent IPv6 + IPv4 → 📡 DNS Query Timeout: 5000ms
- 📍 Return IP directly No DNS needed → 💾 Store Result StrTaskResult
- 📥 Get IP Address First result only → 💾 Store Result StrTaskResult
- 💾 Store Result StrTaskResult → 📋 Log Report ReportSection
- 📋 Log Report ReportSection → Success
- ❌ DNS_LOOKUP_EMPTY_URL → Error
- ❌ DNS_LOOKUP_FAILED → Error
- ❌ DNS_LOOKUP_TIMEOUT → Error

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

# DNS Resolution Strategies

## Strategy 1: FORCE_IPV4

Diagram describing workflow steps.

**Use case**: Force resolution to IPv4 only (legacy systems).

## Strategy 2: FORCE_IPV6

Diagram describing workflow steps.

**Use case**: Force resolution to IPv6 only (modern IPv6-only networks).

## Strategy 3: PREFER_IPV6_FALLBACK_IPV4

Diagram describing workflow steps.

**Use case**: Prefer modern IPv6 but fallback to IPv4 if unavailable.

## Strategy 4: HAPPY_EYEBALLS (RFC 8305)

Diagram describing workflow steps.

**Use case**: Fastest resolution with intelligent fallback (RFC 8305 standard).

## Strategy Comparison

- Strategy: **FORCE_IPV4** | IPv4: ✅ | IPv6: ❌ | Speed: Fast | Use Case: Legacy systems
- Strategy: **FORCE_IPV6** | IPv4: ❌ | IPv6: ✅ | Speed: Fast | Use Case: IPv6-only networks
- Strategy: **PREFER_IPV6_FALLBACK_IPV4** | IPv4: ✅ (fallback) | IPv6: ✅ (preferred) | Speed: Medium | Use Case: Balanced modern networks
- Strategy: **HAPPY_EYEBALLS** | IPv4: ✅ | IPv6: ✅ | Speed: Very Fast | Use Case: Optimized (RFC 8305)

# Parameter details

## 1. Input parameter: `url`

Domain name or IP address to resolve.

### Example

```json
"url": "api.example.com"
```

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

```json
"dns_server": "1.1.1.1"
```

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

```json
"resolve_ops": "HAPPY_EYEBALLS"
```

# Output details

## 1. Result variable: `dns_result_output`

Contains the resolved IP address (IPv4 or IPv6).

### Example

```json
"dns_result_output": "$DNS_IP"
```

# Complete JSON example

```json
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

# Notes

- **Timeout**: All DNS queries have a fixed 5-second timeout.
- **Already IP**: If the input is already an IP address (IPv4 or IPv6), no DNS query is performed and the address is returned immediately.
- **Happy Eyeballs**: Implements RFC 8305 with 250ms stagger between IPv6 and IPv4 queries for optimal performance.
- **DNS Server**: If not specified, the system default DNS server is used (usually from device settings).

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