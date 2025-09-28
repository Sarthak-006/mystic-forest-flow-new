// Minimal ethers.js fallback for offline use
// This is a simplified version for basic functionality

console.log('Loading offline ethers.js fallback...');

// Check if we're in a browser environment
if (typeof window !== 'undefined') {
    // Minimal ethers implementation
    window.ethers = {
        providers: {
            Web3Provider: function (provider) {
                this.provider = provider;
                this.getSigner = function () {
                    return {
                        getAddress: async function () {
                            const accounts = await provider.request({ method: 'eth_accounts' });
                            return accounts[0];
                        }
                    };
                };
                this.getNetwork = async function () {
                    const chainId = await provider.request({ method: 'eth_chainId' });
                    return { chainId: parseInt(chainId, 16) };
                };
            }
        },
        Contract: function (address, abi, provider) {
            this.address = address;
            this.abi = abi;
            this.provider = provider;

            // Basic contract method implementation
            this.createStoryOutcome = async function (endingCategory, score, imageUrl, mangaImageUrl) {
                // This would normally call the smart contract
                // For now, we'll simulate a successful transaction
                console.log('Simulating contract call:', { endingCategory, score, imageUrl, mangaImageUrl });

                // Simulate transaction
                const mockTx = {
                    hash: '0x' + Math.random().toString(16).substr(2, 64),
                    wait: async function () {
                        return {
                            blockNumber: Math.floor(Math.random() * 1000000),
                            events: [{
                                event: 'StoryCreated',
                                args: { storyId: Math.floor(Math.random() * 1000) }
                            }]
                        };
                    }
                };

                return mockTx;
            };

            this.getStoryOutcome = async function (storyId) {
                console.log('Simulating getStoryOutcome for ID:', storyId);
                return {
                    storyId: storyId,
                    endingCategory: 'Test Ending',
                    score: 5,
                    imageUrl: 'https://via.placeholder.com/400x400',
                    mangaImageUrl: 'https://via.placeholder.com/400x400',
                    player: '0x0000000000000000000000000000000000000000',
                    timestamp: Math.floor(Date.now() / 1000)
                };
            };

            this.getTotalStories = async function () {
                return 0;
            };

            this.storyExists = async function (storyId) {
                return false;
            };
        }
    };

    console.log('Offline ethers.js fallback loaded successfully');
} else {
    console.error('Offline ethers.js fallback requires browser environment');
}
