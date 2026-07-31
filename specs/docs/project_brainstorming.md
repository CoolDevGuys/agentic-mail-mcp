The project is intended to be a mcp server that can manage gmail accounts, strongly focused on being used by AI agents such as openclaw or hermes so there must be strict railguards around it to prevent undesired results or security risks.

The suggested project structure is located in @project_structure.md. 
The project must follow DDD principles, combined with vertical slicing and good practices.
The programming language must be python.
Currently there is a `main.py` file that was used as a onetime script to test the gmail integration and it works, it contain hardcoded values and the usage was to fordward messages from one email account to another.
The mcp must allow to search emails in the configured account, it can use several criteria to filter the emails, for example by subject, from, to, date range, by specific senders/recipients, etc.
By default read-only access is configured but the user can allow write access to the account, we need to think on the best railguards to hadle write access with the minimum risks.
The project must be documented and tested.
The mcp must be portable and work on any platform. We need to think on the simplest, fastest and easiest way to distribute it, so it can be used by any ai agent or harness.
Potential features:
- [ ] Gmail integration
- [ ] Email search
- [ ] Email forwarding WITH RAILGUARDS!
- [ ] Email archiving WITH RAILGUARDS!
- [ ] Email deletion WITH RAILGUARDS!
- [ ] Email tagging
- [ ] Email filtering
