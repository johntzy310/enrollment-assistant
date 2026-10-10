# Ethics & Emerging Tech Reflection

1. **Liability & Safeguards:** 
   If the assistant gives a wrong deadline and a student misses enrollment, the school ultimately holds institutional responsibility for the accuracy of published notices. To safeguard against this before a real launch, we would add a human-in-the-loop review queue for flagged low-confidence answers and include a disclaimer advising students to verify critical dates with the physical registrar office.

2. **Training Bias:** 
   Training on only 50 synthetic questions written by a single developer introduces vocabulary and phrasing bias that does not match how real students actually speak, especially considering localized slang, code-switching, and typos. To fix this, we would collect anonymized conversational logs from pilot testing, expand the training set with genuine student prompts, and incorporate data augmentation techniques.

3. **Data Privacy Act of 2012:** 
   Under the Data Privacy Act of 2012, the school must inform users via a clear privacy notice about what data is gathered and how it is processed. The school should avoid storing personally identifiable information (PII) such as student numbers, grades, contact numbers, or sensitive personal records in plain chat logs.

4. **Emerging Tech (IoT):** 
   Integrating Internet of Things (IoT) sensors deployed around campus queues (e.g., smart foot-traffic counters at the Registrar's Office) could extend this assistant to provide real-time wait time estimates to students asking about lines. However, it might not be worth the infrastructure overhead and maintenance cost if standard schedule FAQs already suffice for most user inquiries.
