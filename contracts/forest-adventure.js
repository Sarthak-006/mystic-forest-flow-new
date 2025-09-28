// Import ethers from the ethers.js library
const { ethers } = require('ethers');

// Define the contract ABI
const contractABI = [
    'function createStoryOutcome(string memory _endingCategory, uint256 _score, string memory _imageUrl, string memory _mangaImageUrl) public returns (uint256)',
    'function getStoryOutcome(uint256 _storyId) public view returns (uint256 storyId, string memory endingCategory, uint256 score, string memory imageUrl, string memory mangaImageUrl, address player, uint256 timestamp)',
    'function updateStoryImage(uint256 _storyId, string memory _newImageUrl) public',
    'function getTotalStories() public view returns (uint256)',
    'function storyExists(uint256 _storyId) public view returns (bool)',
    'event StoryCreated(uint256 indexed storyId, address indexed player, string endingCategory, uint256 score)',
    'event StoryUpdated(uint256 indexed storyId, string newImageUrl)'
];

// Define the contract address (replace with your deployed contract address)
const contractAddress = '0xafa6C385c1B6D26Fda55f1a576828B75E9F9FD6c'; // Deployed contract address

// Connect to the Flow network
const provider = new ethers.providers.Web3Provider(window?.ethereum);

// Create a new contract instance
const contract = new ethers.Contract(contractAddress, contractABI, provider);

// Function to create a new story outcome
async function createStoryOutcome(endingCategory, score, imageUrl, mangaImageUrl) {
    try {
        const signer = provider.getSigner();
        const contractWithSigner = contract.connect(signer);

        const tx = await contractWithSigner.createStoryOutcome(
            endingCategory,
            score,
            imageUrl,
            mangaImageUrl
        );

        console.log('Transaction hash:', tx.hash);

        // Wait for transaction to be mined
        const receipt = await tx.wait();
        console.log('Transaction confirmed in block:', receipt.blockNumber);

        // Get the story ID from the event
        const event = receipt.events.find(e => e.event === 'StoryCreated');
        const storyId = event.args.storyId;

        console.log('Story created with ID:', storyId.toString());
        return storyId;
    } catch (error) {
        console.error('Error creating story:', error);
        throw error;
    }
}

// Function to get story outcome details
async function getStoryOutcome(storyId) {
    try {
        const story = await contract.getStoryOutcome(storyId);
        console.log('Story details:', {
            id: story.storyId.toString(),
            ending: story.endingCategory,
            score: story.score.toString(),
            imageUrl: story.imageUrl,
            mangaImageUrl: story.mangaImageUrl,
            player: story.player,
            timestamp: new Date(story.timestamp * 1000).toLocaleString()
        });
        return story;
    } catch (error) {
        console.error('Error getting story:', error);
        throw error;
    }
}

// Function to get total number of stories
async function getTotalStories() {
    try {
        const total = await contract.getTotalStories();
        console.log('Total stories:', total.toString());
        return total;
    } catch (error) {
        console.error('Error getting total stories:', error);
        throw error;
    }
}

// Function to check if a story exists
async function checkStoryExists(storyId) {
    try {
        const exists = await contract.storyExists(storyId);
        console.log('Story exists:', exists);
        return exists;
    } catch (error) {
        console.error('Error checking story existence:', error);
        throw error;
    }
}

// Example usage
async function example() {
    try {
        // Check total stories
        await getTotalStories();

        // Create a new story outcome
        const storyId = await createStoryOutcome(
            "Heroic Savior",
            8,
            "https://image.pollinations.ai/prompt/heroic%20adventure",
            "https://image.pollinations.ai/prompt/manga%20style%20hero"
        );

        // Get the story details
        await getStoryOutcome(storyId);

        // Check if story exists
        await checkStoryExists(storyId);

    } catch (error) {
        console.error('Example failed:', error);
    }
}

// Export functions for use in your main application
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createStoryOutcome,
        getStoryOutcome,
        getTotalStories,
        checkStoryExists,
        contractABI
    };
}
