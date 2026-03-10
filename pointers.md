
### Storage Metrics Explained

* **Checksum Integrity (35% - Critical Data Loss):** When a file is saved, the system calculates a unique mathematical string (a hash) representing that exact data. When the file is read later, the system recalculates the hash. If the hashes do not match, a "Checksum Mismatch" has occurred. This means the data has been silently corrupted (bit rot) by a software bug or cosmic radiation. It is the most critical metric because it means the data you are serving is actively broken.
* **Replica Availability (25% - Redundancy Risk):**  Cloud systems rarely store just one copy of a file. They usually store three copies across different physical servers (nodes) so that if one server catches fire, the data survives. This metric tracks how many of those required copies are currently online and reachable. A drop means a node has failed or a network cable was cut.
* **Node Temperature (15% - Physical Hardware Stress):** Hard drives and SSDs have strict thermal operating limits. If a server's cooling fan fails and the temperature spikes above 50°C–60°C, the physical components warp, and the drive's lifespan drops dramatically. It is a leading indicator of an impending hardware crash.
* **Read Latency (15% - Performance Degradation):** This measures how many milliseconds (ms) it takes for the disk to find and return the requested data. Healthy enterprise disks return data in under 15ms. If this spikes to 100ms+, it means the disk's physical read-head is struggling, or the internal controller is choking on read errors.
* **SMART Errors (10% - Mechanical Wear):** "SMART" (Self-Monitoring, Analysis, and Reporting Technology) is a system built into modern drives. "Uncorrectable errors" occur when the drive tries to read a sector of the disk, fails, tries to use hardware error correction, and still fails. The drive is effectively telling you, "I am physically dying."


Here is the breakdown of the three fault scenarios your simulator generates, the real-world event they represent, and exactly how the telemetry data changes.

### 1. Gradual Hardware Degradation ("The Slow Death")

* **The Real-World Concept:** A physical hard drive or SSD is slowly dying. Perhaps the cooling fan in the server rack has failed, causing the drive to overheat. As it overheats, the physical read-write heads struggle to scan the magnetic platters, causing high latency and throwing hardware-level errors.
* **The Metric Changes:** This is a **linear** change over time.
* `node_temperature_c`: Steadily climbs upward (e.g., from a healthy 35°C to a dangerous 60°C+).
* `disk_read_latency_ms`: Creeps upward and spikes randomly (e.g., from 12ms to 200ms) as the disk struggles to perform I/O operations.
* `smart_uncorrectable_errors`: Increments periodically (e.g., 0 $\rightarrow$ 1 $\rightarrow$ 2 $\rightarrow$ 3) as the hardware encounters bad sectors it cannot fix.
* *Logical Metrics (Replicas, Checksum):* Remain perfectly healthy.


* **The FHS Impact:** The File Health Score (FHS) drains slowly. It will slide from 99 down to 90, 85, and eventually cross the 75 threshold, triggering a proactive alert *before* the drive completely dies.

### 2. Sudden Network Partition ("The Spike")

* **The Real-World Concept:** A top-of-rack network switch suddenly loses power, or a fiber optic cable is accidentally unplugged. The physical storage nodes are perfectly healthy, but they can suddenly no longer talk to each other to synchronize data.
* **The Metric Changes:** This is a **step-function** (instant) change.
* `replica_availability_ratio`: Instantly plummets. If you require 3 copies of a file and 1 node vanishes from the network, this ratio drops immediately from `1.0` (100%) to `0.66` (66%).
* *Physical Metrics (Temp, Latency, Errors):* Remain perfectly healthy. The drives themselves are fine; they just lack network access.


* **The FHS Impact:** The FHS drops like a rock. Because replica availability accounts for 25% of the total score, losing a third of your replicas instantly shaves about 8.5 points off the score in a single second, immediately triggering a critical network alert.

### 3. Silent Data Corruption ("The Bit Flip")

* **The Real-World Concept:** Also known as "bit rot." A cosmic ray strikes the RAM, or a rare software bug writes bad data to the disk without throwing an error. The hardware is fine, the network is fine, but the actual data inside the file has been altered.
* **The Metric Changes:** This is a **stealth** change.
* `checksum_mismatch_flag`: Instantly flips from `0` to `1`. The system calculated the cryptographic hash of the file and realized it no longer matches the expected signature.
* *Physical Metrics:* Perfectly normal.
* *Network Metrics:* Perfectly normal.


* **The FHS Impact:** Devastating. Checksum integrity is weighted at 35% because serving corrupted data is the worst-case scenario for a cloud provider. When this flag flips to 1, the FHS instantly loses 35 points, dropping from 99 straight down to 64, forcing an immediate system halt to quarantine the corrupted file.

---

### Why this makes your LLM Engine brilliant:

By looking at these three distinct "signatures," you can see exactly how the LLM will diagnose the root cause:

* If the LLM sees high heat and SMART errors, it will output `Action: MIGRATE_PRIMARY_NODE`.
* If the LLM sees a dropped replica but normal temperatures, it will output `Action: REBUILD_REPLICA`.
* If the LLM sees a checksum mismatch but everything else is fine, it will output `Action: RESTORE_FROM_SNAPSHOT`.

