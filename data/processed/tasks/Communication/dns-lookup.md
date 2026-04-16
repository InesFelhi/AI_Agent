# DNS Lookup

## Summary

- **Internal name**: `DnsLookup`
- **Category**: Communication
- **Purpose**: Resolve a domain name to an IP address using configurable DNS resolution strategies. Returns the resolved IP address as a string.
- **Task type**: Normal

## Compatibility

- **Minimum AndroMate version**: `{{ ANDROMATE_FIRST_VERSION }}`
- **Maximum AndroMate version**: `{{ ANDROMATE_CURRENT_VERSION }}`
- **Minimum Android**: `{{ ANDROMATE_MIN_APP_SDK }}`
- **Maximum Android tested**: `{{ ANDROID_CURRENT_APP_SDK }}`
- **Required permissions**:
  - `INTERNET`
  - `ACCESS_NETWORK_STATE`

## Detailed description

The **DNS Lookup** task resolves the domain name or IP address provided in `url` to a resolved IP address. If the input is already a valid IPv4 or IPv6 address, no DNS query is performed — the address is returned directly.

For actual domain resolution, the task applies the strategy selected by `resolve_ops` (an integer key). An optional `dns_server` can be specified; if empty, the system default DNS server is used. All DNS queries have a fixed timeout of 5000 ms.

On success, the resolved IP address string is stored in `value_output` from `StrTaskResult`.

## Input parameters

- Parameter: `url` | Type: String | Required: Yes | Possible values: Domain name or IP address to resolve — supports `$variable` | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `dns_server` | Type: String | Required: No | Possible values: Custom DNS server IP address — empty string uses system default | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `""`
- Parameter: `resolve_ops` | Type: Integer | Required: No | Possible values: Resolution strategy: `1` = FORCE_IPV4, `2` = FORCE_IPV6, `3` = PREFER_IPV6_FALLBACK_IPV4, `4` = HAPPY_EYEBALLS | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `0` (PREFER_IPV6_FALLBACK_IPV4)

### `resolve_ops` strategy keys

- Value: `1` | Strategy: FORCE_IPV4 | Description: Query A records only
- Value: `2` | Strategy: FORCE_IPV6 | Description: Query AAAA records only
- Value: `3` | Strategy: PREFER_IPV6_FALLBACK_IPV4 | Description: Try IPv6 first, fallback to IPv4 if not found
- Value: `4` | Strategy: HAPPY_EYEBALLS | Description: RFC 8305 — concurrent IPv6 + IPv4 queries
- Value: `0` or omitted | Strategy: PREFER_IPV6_FALLBACK_IPV4 | Description: Default behavior

## Output parameters

- Field: `value_output` | Type: String | Trigger condition: Always on success — resolved IP address | Android Compatibility: {{ ANDROMATE_MIN_APP_SDK }} → {{ ANDROID_CURRENT_APP_SDK }} | AndroMate Compatibility: {{ ANDROMATE_FIRST_VERSION }} → {{ ANDROMATE_CURRENT_VERSION }} | Default: `<ANDROMATE_NULL_VALUE>`

## Exceptions

- Code: `DNS-LOOK-UP-001` | Exception Name: Empty URL | Description: The `url` field is empty (from `AndromateExceptionTypes.DNS_LOOKUP_EMPTY_URL`).
- Code: `DNS-LOOK-UP-002` | Exception Name: DNS Resolution Failed | Description: DNS lookup failed for the given domain — no A/AAAA records found or DNS server error (from `AndromateExceptionTypes.DNS_LOOKUP_FAILED`).

## Execution flowchart

Diagram Nodes:
- ResolveParams: 🔄 Resolve url, dns_server,\nresolve_ops
- E1: ❌ DNS-LOOK-UP-001\nEmpty URL
- ReturnIP: 📍 Return IP directly\nNo DNS query performed
- ForceIPV4: 🔍 Query A records only
- ForceIPV6: 🔍 Query AAAA records only
- PreferIPV6: 🔄 Try IPv6 first\nfallback to IPv4
- HappyEyeballs: ⚡ RFC 8305\nconcurrent IPv6 + IPv4
- DNSQuery: 📡 DNS Query\nTimeout: 5000ms
- StoreResult: 💾 Set value_output\nStrTaskResult
- GetIP: 📥 Extract resolved IP address
- E2: ❌ DNS-LOOK-UP-002\nDNS Resolution Failed
- LogReport: 📋 Log report

Workflow Flow:
- 🔄 Resolve url, dns_server,\nresolve_ops → ValidateURL
- 🔍 Query A records only → 📡 DNS Query\nTimeout: 5000ms
- 🔍 Query AAAA records only → 📡 DNS Query\nTimeout: 5000ms
- 🔄 Try IPv6 first\nfallback to IPv4 → 📡 DNS Query\nTimeout: 5000ms
- ⚡ RFC 8305\nconcurrent IPv6 + IPv4 → 📡 DNS Query\nTimeout: 5000ms
- 📍 Return IP directly\nNo DNS query performed → 💾 Set value_output\nStrTaskResult
- 📥 Extract resolved IP address → 💾 Set value_output\nStrTaskResult
- 💾 Set value_output\nStrTaskResult → 📋 Log report
- 📋 Log report → Success
- ❌ DNS-LOOK-UP-001\nEmpty URL → Error
- ❌ DNS-LOOK-UP-002\nDNS Resolution Failed → Error

**How it works:**

1. **Resolve parameters**: `url`, `dns_server`, and `resolve_ops` are resolved from the workflow context
2. **Validate URL**: throws `DNS-LOOK-UP-001` if `url` is empty
3. **Check if already IP**: if the input is already a valid IPv4 or IPv6 address, it is returned directly in `value_output` — no DNS query is performed
4. **Select resolution strategy**: chooses the DNS resolution strategy based on the `resolve_ops` integer value
5. **DNS query**: performs the DNS lookup with a fixed 5000 ms timeout; uses `dns_server` if specified, otherwise uses the system default
6. **On failure**: throws `DNS-LOOK-UP-002`
7. **Extract IP**: retrieves the resolved IP address
8. **Store result**: sets `value_output` with the resolved IP string
9. **Result**: returns `StrTaskResult`

## Code examples

### Example 1 — Resolve a domain with default strategy

```json
{
  "DnsLookup": [
    {
      "id": "1",
      "title": "Resolve API domain",
      "url": "api.example.com",
      "value_output": "$resolved_ip"
    }
  ]
}
```

### Example 2 — Force IPv4 resolution

```json
{
  "DnsLookup": [
    {
      "id": "2",
      "title": "Force IPv4 resolution",
      "url": "api.example.com",
      "resolve_ops": 1,
      "value_output": "$ipv4_address"
    }
  ]
}
```

### Example 3 — Custom DNS server with Happy Eyeballs

```json
{
  "DnsLookup": [
    {
      "id": "3",
      "title": "Happy Eyeballs with custom DNS",
      "url": "$domain_to_resolve",
      "dns_server": "1.1.1.1",
      "resolve_ops": 4,
      "value_output": "$resolved_ip"
    }
  ]
}
```

### Example 4 — Force IPv6 with custom DNS

```json
{
  "DnsLookup": [
    {
      "id": "4",
      "title": "IPv6 only resolution",
      "url": "ipv6.example.com",
      "dns_server": "8.8.8.8",
      "resolve_ops": 2,
      "value_output": "$ipv6_address"
    }
  ]
}
```

## Input parameter details

### 1. `url` — Domain or IP to resolve

The domain name or IP address to process. If already a valid IPv4 or IPv6 address, returned directly without any DNS query. Supports `$workflow_variable` references.

- Valid: `api.example.com` | Behavior: DNS query performed
- Valid: `192.168.1.1` | Behavior: Returned directly (no DNS query)
- Valid: `2001:db8::1` | Behavior: Returned directly (no DNS query)
- Valid: `$domain` | Behavior: Resolved from variable, then processed
- Valid: `""` | Behavior: Throws `DNS-LOOK-UP-001`

- **Default**: `""`

### 2. `dns_server` — Custom DNS server

The IP address of a custom DNS server to use for resolution. If empty (`""`), the system default DNS server is used (from device network settings).

- Example: `"8.8.8.8"` | Description: Google DNS
- Example: `"1.1.1.1"` | Description: Cloudflare DNS
- Example: `"208.67.222.222"` | Description: OpenDNS
- Example: `""` | Description: System default (device DNS settings)

- **Default**: `""` (system default)

### 3. `resolve_ops` — Resolution strategy

An integer key selecting the DNS resolution strategy. Default behavior (value `0` or omitted) is PREFER_IPV6_FALLBACK_IPV4.

- Value: `1` | Strategy: FORCE_IPV4 | Description: A records only — IPv4 address returned
- Value: `2` | Strategy: FORCE_IPV6 | Description: AAAA records only — IPv6 address returned
- Value: `3` | Strategy: PREFER_IPV6_FALLBACK_IPV4 | Description: Try IPv6 first; fallback to IPv4 if no AAAA found
- Value: `4` | Strategy: HAPPY_EYEBALLS | Description: RFC 8305 concurrent queries — fastest response wins
- Value: `0` or omitted | Strategy: PREFER_IPV6_FALLBACK_IPV4 | Description: Default

- **Type**: Integer
- **Default**: `0` (PREFER_IPV6_FALLBACK_IPV4)

## Output parameter details

### `value_output` — Resolved IP address

Stores the resolved IP address string (from `StrTaskResult`) in the specified workflow variable.

- For domain inputs: the IP address resolved by DNS
- For IP inputs already passed in: the same IP address returned directly
- May be IPv4 (e.g. `"93.184.216.34"`) or IPv6 (e.g. `"2606:2800:220:1:248:1893:25c8:1946"`) depending on the resolution strategy

## DNS Resolution Strategies

### Strategy 1: FORCE_IPV4 (`resolve_ops: 1`)

Queries only A records. Returns the first IPv4 address found. Throws `DNS-LOOK-UP-002` if no A records are available.

**Use case**: Legacy systems that require IPv4 only.

### Strategy 2: FORCE_IPV6 (`resolve_ops: 2`)

Queries only AAAA records. Returns the first IPv6 address found. Throws `DNS-LOOK-UP-002` if no AAAA records are available.

**Use case**: IPv6-only network environments.

### Strategy 3: PREFER_IPV6_FALLBACK_IPV4 (`resolve_ops: 3` or default)

First queries AAAA records. If an IPv6 address is found, returns it. If no AAAA records exist, falls back to querying A records. Throws `DNS-LOOK-UP-002` if neither is found.

**Use case**: Modern networks preferring IPv6 with backward compatibility.

### Strategy 4: HAPPY_EYEBALLS (`resolve_ops: 4`)

Implements RFC 8305. Starts an IPv6 (AAAA) query, then after a short delay starts an IPv4 (A) query concurrently. The first query to return a result wins. Throws `DNS-LOOK-UP-002` if both fail.

**Use case**: Optimal performance on any network type.

### Strategy Comparison

- Strategy: FORCE_IPV4 | `resolve_ops`: `1` | IPv4: ✅ | IPv6: ❌ | Use Case: Legacy systems
- Strategy: FORCE_IPV6 | `resolve_ops`: `2` | IPv4: ❌ | IPv6: ✅ | Use Case: IPv6-only networks
- Strategy: PREFER_IPV6_FALLBACK_IPV4 | `resolve_ops`: `3` or `0` | IPv4: ✅ (fallback) | IPv6: ✅ (preferred) | Use Case: Balanced modern networks
- Strategy: HAPPY_EYEBALLS | `resolve_ops`: `4` | IPv4: ✅ | IPv6: ✅ | Use Case: Optimized (RFC 8305)

## Complete JSON example

```json
{
  "DnsLookup": [
    {
      "id": "1",
      "title": "DNS Lookup",
      "url": "api.example.com",
      "dns_server": "8.8.8.8",
      "resolve_ops": 4,
      "value_output": "$RESOLVED_IP"
    }
  ]
}
```